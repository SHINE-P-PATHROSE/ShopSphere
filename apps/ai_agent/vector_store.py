"""
Vector Store Service (RAG Layer).

Architectural decision: ChromaDB as default (embedded, zero-infra, runs
in-process). In production, swap to Qdrant or Pinecone by changing
AI_VECTOR_BACKEND in settings. The interface is identical — only the
backend changes.

Collections:
  - shopsphere_products    — product titles, descriptions, specs
  - shopsphere_reviews     — customer reviews for sentiment/search
  - shopsphere_faqs        — FAQ Q&A pairs
  - shopsphere_support     — support ticket knowledge base
  - shopsphere_cms         — CMS page content
"""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# Collection name constants
COLLECTION_PRODUCTS = "shopsphere_products"
COLLECTION_REVIEWS = "shopsphere_reviews"
COLLECTION_FAQS = "shopsphere_faqs"
COLLECTION_SUPPORT = "shopsphere_support"
COLLECTION_CMS = "shopsphere_cms"


def _get_chroma_client() -> Any:
    """Return a persistent ChromaDB client."""
    try:
        import chromadb
        from chromadb.config import Settings as ChromaSettings
    except ImportError:
        raise ImportError(
            "ChromaDB not installed. Run: pip install chromadb"
        )

    persist_dir = str(
        Path(settings.BASE_DIR) / getattr(settings, "AI_VECTOR_PERSIST_DIR", "data/chroma")
    )

    return chromadb.PersistentClient(
        path=persist_dir,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def _get_qdrant_client() -> Any:
    """Return a Qdrant client (production)."""
    try:
        from qdrant_client import QdrantClient
    except ImportError:
        raise ImportError("Run: pip install qdrant-client")

    url = getattr(settings, "QDRANT_URL", "http://localhost:6333")
    api_key = getattr(settings, "QDRANT_API_KEY", None)
    return QdrantClient(url=url, api_key=api_key)


def get_vector_store(collection_name: str) -> Any:
    """
    Return a LangChain VectorStore wrapper for the given collection.
    Uses AI_VECTOR_BACKEND setting (chroma|qdrant).
    """
    from apps.ai_agent.providers import get_embeddings_client

    backend = getattr(settings, "AI_VECTOR_BACKEND", "chroma").lower()
    embeddings = get_embeddings_client()

    if backend == "chroma":
        try:
            from langchain_chroma import Chroma
        except ImportError:
            raise ImportError("Run: pip install langchain-chroma")

        client = _get_chroma_client()
        return Chroma(
            client=client,
            collection_name=collection_name,
            embedding_function=embeddings,
        )
    elif backend == "qdrant":
        try:
            from langchain_qdrant import QdrantVectorStore
        except ImportError:
            raise ImportError("Run: pip install langchain-qdrant")

        client = _get_qdrant_client()
        return QdrantVectorStore(
            client=client,
            collection_name=collection_name,
            embedding=embeddings,
        )
    else:
        raise ValueError(f"Unknown vector backend: '{backend}'")


def embed_product(product_id: int) -> bool:
    """
    Embed a single product into the products vector store.
    Called by Celery task after product create/update.
    """
    from apps.ai_agent.models import VectorDocument
    from apps.products.models import Product

    try:
        product = Product.objects.select_related("category", "brand", "store").get(
            pk=product_id, status="APPROVED"
        )
    except Product.DoesNotExist:
        logger.warning("embed_product: Product %s not found or not approved.", product_id)
        return False

    # Build rich document text
    text = _build_product_text(product)
    checksum = _sha256(text)

    # Check if unchanged
    existing = VectorDocument.objects.filter(
        content_type="product", object_id=str(product_id), chunk_index=0
    ).first()
    if existing and existing.checksum == checksum and existing.is_indexed:
        logger.debug("Product %s unchanged, skipping re-embed.", product_id)
        return True

    try:
        store = get_vector_store(COLLECTION_PRODUCTS)
        doc_id = f"product_{product_id}"

        store.add_texts(
            texts=[text],
            metadatas=[{
                "product_id": product_id,
                "title": product.title,
                "category": product.category.name,
                "brand": product.brand.name if product.brand else "",
                "store": product.store.name,
                "price": float(product.base_price),
                "rating": float(product.average_rating),
                "in_stock": product.in_stock,
            }],
            ids=[doc_id],
        )

        # Update metadata in DB
        VectorDocument.objects.update_or_create(
            content_type="product",
            object_id=str(product_id),
            chunk_index=0,
            defaults={
                "collection_name": COLLECTION_PRODUCTS,
                "text_preview": text[:500],
                "checksum": checksum,
                "is_indexed": True,
                "indexed_at": timezone.now(),
                "embedding_model": getattr(settings, "AI_EMBEDDINGS_MODEL", ""),
            },
        )
        logger.info("Product %s embedded successfully.", product_id)
        return True

    except Exception as exc:
        logger.error("Failed to embed product %s: %s", product_id, exc)
        return False


def semantic_search_products(
    query: str,
    k: int = 8,
    filters: dict | None = None,
) -> list[dict[str, Any]]:
    """
    Perform semantic search over the products collection.
    Returns list of dicts with product metadata and relevance score.
    """
    try:
        store = get_vector_store(COLLECTION_PRODUCTS)
        results = store.similarity_search_with_relevance_scores(query, k=k)
        return [
            {
                "product_id": doc.metadata.get("product_id"),
                "title": doc.metadata.get("title"),
                "score": float(score),
                "metadata": doc.metadata,
            }
            for doc, score in results
            if score >= getattr(settings, "AI_SIMILARITY_THRESHOLD", 0.3)
        ]
    except Exception as exc:
        logger.error("Semantic search failed: %s", exc)
        return []


def embed_faq(question: str, answer: str, faq_id: str) -> bool:
    """Embed an FAQ Q&A pair for RAG-based question answering."""
    try:
        store = get_vector_store(COLLECTION_FAQS)
        text = f"Q: {question}\nA: {answer}"
        store.add_texts(
            texts=[text],
            metadatas=[{"faq_id": faq_id, "question": question}],
            ids=[f"faq_{faq_id}"],
        )
        return True
    except Exception as exc:
        logger.error("Failed to embed FAQ %s: %s", faq_id, exc)
        return False


def search_faqs(query: str, k: int = 3) -> list[dict[str, Any]]:
    """Search the FAQ knowledge base for relevant answers."""
    try:
        store = get_vector_store(COLLECTION_FAQS)
        results = store.similarity_search(query, k=k)
        return [
            {"text": doc.page_content, "metadata": doc.metadata}
            for doc in results
        ]
    except Exception as exc:
        logger.error("FAQ search failed: %s", exc)
        return []


def _build_product_text(product: Any) -> str:
    """Build rich text representation of a product for embedding."""
    parts = [
        f"Product: {product.title}",
        f"Category: {product.category.name}",
    ]
    if product.brand:
        parts.append(f"Brand: {product.brand.name}")
    if product.short_description:
        parts.append(f"Summary: {product.short_description}")
    if product.description:
        parts.append(f"Description: {product.description[:800]}")
    parts.append(f"Price: ₹{product.base_price}")
    parts.append(f"Store: {product.store.name}")
    if product.tags.exists():
        tags = ", ".join(product.tags.values_list("name", flat=True)[:10])
        parts.append(f"Tags: {tags}")
    return "\n".join(parts)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()
