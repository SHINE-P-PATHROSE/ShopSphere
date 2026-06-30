"""
Vendor Agent Tools.

Tools for AI-assisted product management: auto-generate titles,
descriptions, SEO content, tags, pricing suggestions, and
inventory/sales insights for approved vendors.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Shared LLM call helper (lazy to avoid import-time errors when keys not set)
def _llm_generate(prompt: str, max_tokens: int = 512) -> str:
    """Run a single LLM generation and return the string response."""
    from apps.ai_agent.providers import get_llm_client
    from langchain_core.messages import HumanMessage

    llm = get_llm_client()
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()


def generate_product_title(
    category: str,
    brand: str,
    key_features: str,
    target_audience: str = "",
) -> dict[str, Any]:
    """
    Generate an SEO-optimised product title using AI.

    Args:
        category: Product category (e.g. 'Running Shoes').
        brand: Brand name.
        key_features: Comma-separated key features (e.g. 'waterproof, lightweight').
        target_audience: Optional target audience description.
    """
    prompt = (
        f"Generate 3 SEO-optimised product titles for an e-commerce listing.\n"
        f"Category: {category}\n"
        f"Brand: {brand}\n"
        f"Key features: {key_features}\n"
        f"Target audience: {target_audience or 'general customers'}\n\n"
        "Requirements:\n"
        "- Keep each title under 80 characters\n"
        "- Include brand, main feature, and category keyword\n"
        "- Make it click-worthy and clear\n"
        "- Format: numbered list, one title per line\n"
        "Return only the titles, no explanations."
    )

    try:
        raw = _llm_generate(prompt, max_tokens=300)
        titles = [
            line.strip().lstrip("123456789.-) ")
            for line in raw.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        return {
            "success": True,
            "titles": titles[:3],
            "recommended": titles[0] if titles else "",
        }
    except Exception as exc:
        logger.error("generate_product_title error: %s", exc)
        return {"success": False, "error": str(exc), "titles": []}


def generate_product_description(
    product_title: str,
    category: str,
    key_features: str,
    target_audience: str = "",
    tone: str = "professional",
) -> dict[str, Any]:
    """
    Generate a compelling product description with SEO meta description.

    Args:
        product_title: The product title.
        category: Product category.
        key_features: Key features as comma-separated string.
        target_audience: Optional target audience.
        tone: Writing tone — professional, casual, luxury, technical.
    """
    prompt = (
        f"Write a compelling product description for an Indian e-commerce platform.\n\n"
        f"Product: {product_title}\n"
        f"Category: {category}\n"
        f"Key Features: {key_features}\n"
        f"Target Audience: {target_audience or 'general customers'}\n"
        f"Tone: {tone}\n\n"
        "Output the following sections:\n"
        "1. SHORT DESCRIPTION (1 sentence, max 160 chars, for meta)\n"
        "2. MAIN DESCRIPTION (150-250 words with benefits and use cases)\n"
        "3. KEY HIGHLIGHTS (5 bullet points)\n\n"
        "Use ₹ for Indian pricing context if mentioning price. "
        "Do not include any pricing. Return structured text only."
    )

    try:
        raw = _llm_generate(prompt, max_tokens=800)

        # Parse sections
        sections = {"short": "", "main": "", "highlights": []}
        current = None
        buffer: list[str] = []

        for line in raw.splitlines():
            if "SHORT DESCRIPTION" in line.upper():
                current = "short"
                buffer = []
            elif "MAIN DESCRIPTION" in line.upper():
                if current == "short":
                    sections["short"] = " ".join(buffer).strip()
                current = "main"
                buffer = []
            elif "KEY HIGHLIGHTS" in line.upper():
                if current == "main":
                    sections["main"] = "\n".join(buffer).strip()
                current = "highlights"
                buffer = []
            elif line.strip() and current:
                buffer.append(line.strip())

        if current == "highlights":
            sections["highlights"] = [
                b.lstrip("-•* ")
                for b in buffer
                if b.strip()
            ][:5]
        elif current == "main" and not sections["main"]:
            sections["main"] = "\n".join(buffer).strip()

        return {
            "success": True,
            "short_description": sections["short"] or raw[:160],
            "description": sections["main"] or raw,
            "highlights": sections["highlights"],
        }

    except Exception as exc:
        logger.error("generate_product_description error: %s", exc)
        return {"success": False, "error": str(exc)}


def generate_product_tags(
    product_title: str,
    category: str,
    description: str = "",
) -> dict[str, Any]:
    """
    Auto-generate relevant search tags for a product.

    Args:
        product_title: The product title.
        category: Product category.
        description: Optional product description for context.
    """
    prompt = (
        f"Generate 10-15 relevant search tags for this product on an Indian marketplace.\n\n"
        f"Product: {product_title}\n"
        f"Category: {category}\n"
        f"Description: {description[:300] if description else 'N/A'}\n\n"
        "Requirements:\n"
        "- Mix short (1-2 word) and long-tail (3-4 word) tags\n"
        "- Include common Indian search patterns\n"
        "- Include synonyms and related terms\n"
        "- All lowercase, comma-separated\n"
        "Return only the tags as a single comma-separated line."
    )

    try:
        raw = _llm_generate(prompt, max_tokens=200)
        tags = [
            t.strip().lower()
            for t in raw.replace("\n", ",").split(",")
            if t.strip() and len(t.strip()) < 50
        ]
        return {
            "success": True,
            "tags": tags[:15],
        }
    except Exception as exc:
        logger.error("generate_product_tags error: %s", exc)
        return {"success": False, "error": str(exc), "tags": []}


def suggest_pricing(
    product_title: str,
    category: str,
    cost_price: float,
    competitor_prices: list[float] | None = None,
) -> dict[str, Any]:
    """
    Suggest optimal pricing for a product based on cost and market context.

    Args:
        product_title: Product name.
        category: Product category.
        cost_price: Your cost/purchase price in INR.
        competitor_prices: Optional list of competitor prices in INR.
    """
    comp_str = ""
    if competitor_prices:
        prices = [f"₹{p:,.0f}" for p in competitor_prices[:5]]
        comp_str = f"Competitor prices: {', '.join(prices)}\n"

    prompt = (
        f"Suggest optimal retail pricing for this product on an Indian marketplace.\n\n"
        f"Product: {product_title}\n"
        f"Category: {category}\n"
        f"Cost Price: ₹{cost_price:,.0f}\n"
        f"{comp_str}\n"
        "Provide:\n"
        "1. RECOMMENDED PRICE: ₹X (with brief justification)\n"
        "2. COMPARE AT PRICE (original/MRP): ₹X (for showing discount)\n"
        "3. MINIMUM VIABLE PRICE: ₹X (floor price to stay profitable)\n"
        "4. PRICING STRATEGY: 1-2 sentences on approach\n\n"
        "Consider standard Indian marketplace margins (20-40%) and customer psychology."
    )

    try:
        raw = _llm_generate(prompt, max_tokens=300)
        return {
            "success": True,
            "pricing_advice": raw,
            "cost_price": cost_price,
            "minimum_margin_20pct": round(cost_price * 1.2, 2),
            "minimum_margin_30pct": round(cost_price * 1.3, 2),
        }
    except Exception as exc:
        logger.error("suggest_pricing error: %s", exc)
        return {"success": False, "error": str(exc)}


def get_inventory_insights(vendor_store_id: int, days: int = 30) -> dict[str, Any]:
    """
    Analyse inventory health for a vendor's store — identify low stock,
    overstocked, and fast-moving items.

    Args:
        vendor_store_id: The Store model ID for the vendor.
        days: Lookback period in days for sales velocity.
    """
    from datetime import timedelta

    from django.db.models import F, Sum
    from django.utils import timezone

    from apps.orders.models import OrderItem
    from apps.products.models import ProductVariant

    try:
        since = timezone.now() - timedelta(days=days)

        variants = ProductVariant.objects.filter(
            product__store_id=vendor_store_id,
            product__status="APPROVED",
            is_active=True,
        ).select_related("product")

        # Sales velocity per variant
        sales_data = (
            OrderItem.objects.filter(
                store_id=vendor_store_id,
                created_at__gte=since,
            )
            .values("variant_id")
            .annotate(units_sold=Sum("quantity"))
        )
        sales_map = {s["variant_id"]: s["units_sold"] for s in sales_data}

        low_stock = []
        out_of_stock = []
        fast_movers = []

        for v in variants:
            sold = sales_map.get(v.pk, 0)
            daily_velocity = sold / days if days > 0 else 0
            days_until_stockout = int(v.stock / daily_velocity) if daily_velocity > 0 else 999

            if v.stock == 0:
                out_of_stock.append({"sku": v.sku, "title": v.product.title})
            elif v.stock <= v.low_stock_threshold:
                low_stock.append({
                    "sku": v.sku,
                    "title": v.product.title,
                    "stock": v.stock,
                    "days_left": days_until_stockout,
                    "units_sold": sold,
                })
            if sold > 10:
                fast_movers.append({
                    "sku": v.sku,
                    "title": v.product.title,
                    "units_sold": sold,
                    "daily_velocity": round(daily_velocity, 2),
                })

        fast_movers.sort(key=lambda x: x["units_sold"], reverse=True)

        return {
            "success": True,
            "period_days": days,
            "low_stock_count": len(low_stock),
            "out_of_stock_count": len(out_of_stock),
            "low_stock_items": low_stock[:10],
            "out_of_stock_items": out_of_stock[:10],
            "fast_movers": fast_movers[:5],
        }

    except Exception as exc:
        logger.error("get_inventory_insights error: %s", exc)
        return {"success": False, "error": str(exc)}


def get_sales_analysis(vendor_store_id: int, days: int = 30) -> dict[str, Any]:
    """
    Generate a sales performance analysis for a vendor's store.

    Args:
        vendor_store_id: The Store model ID.
        days: Analysis period in days.
    """
    from datetime import timedelta
    from decimal import Decimal

    from django.db.models import Count, Sum
    from django.utils import timezone

    from apps.orders.models import OrderItem

    try:
        since = timezone.now() - timedelta(days=days)

        items = OrderItem.objects.filter(
            store_id=vendor_store_id,
            created_at__gte=since,
        ).exclude(order__status="CANCELLED")

        revenue = items.aggregate(total=Sum("total"))["total"] or Decimal("0")
        units_sold = items.aggregate(total=Sum("quantity"))["total"] or 0
        order_count = items.values("order").distinct().count()

        top_products = (
            items.values("variant__product__title")
            .annotate(units=Sum("quantity"), rev=Sum("total"))
            .order_by("-rev")[:5]
        )

        return {
            "success": True,
            "period_days": days,
            "total_revenue": float(revenue),
            "total_units": units_sold,
            "total_orders": order_count,
            "avg_order_value": float(revenue / order_count) if order_count else 0,
            "top_products": [
                {
                    "title": p["variant__product__title"],
                    "units": p["units"],
                    "revenue": float(p["rev"]),
                }
                for p in top_products
            ],
        }

    except Exception as exc:
        logger.error("get_sales_analysis error: %s", exc)
        return {"success": False, "error": str(exc)}
