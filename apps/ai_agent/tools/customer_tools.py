"""
Customer Agent Tools.

Each function is decorated with @tool from langchain_core so LangGraph
agents can call them via function calling. All tools are stateless —
they accept plain Python types and return JSON-serializable dicts.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def search_products_semantic(query: str, category: str = "", max_results: int = 6) -> dict[str, Any]:
    """
    Search for products using semantic/vector search.
    Returns a list of relevant products with titles, prices, and ratings.

    Args:
        query: Natural language search query from the customer.
        category: Optional category slug to filter results.
        max_results: Maximum number of results to return (default 6).
    """
    from apps.ai_agent.vector_store import semantic_search_products

    try:
        results = semantic_search_products(query, k=max_results)

        if not results:
            # Fall back to keyword search
            from apps.products.models import Product
            from django.db.models import Q

            qs = Product.objects.filter(status="APPROVED").select_related(
                "store", "category", "brand"
            )
            if category:
                qs = qs.filter(category__slug=category)
            qs = qs.filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            )[:max_results]

            results = [
                {
                    "product_id": p.pk,
                    "title": p.title,
                    "score": 0.5,
                    "metadata": {
                        "price": float(p.base_price),
                        "rating": float(p.average_rating),
                        "store": p.store.name,
                        "category": p.category.name,
                    },
                }
                for p in qs
            ]

        return {
            "success": True,
            "query": query,
            "count": len(results),
            "products": results,
        }

    except Exception as exc:
        logger.error("search_products_semantic error: %s", exc)
        return {"success": False, "error": str(exc), "products": []}


def get_product_details(product_id: int) -> dict[str, Any]:
    """
    Get detailed information about a specific product including variants,
    images, specifications, and recent reviews.

    Args:
        product_id: The integer ID of the product.
    """
    from apps.products.models import Product

    try:
        product = Product.objects.filter(pk=product_id, status="APPROVED").select_related(
            "store", "category", "brand"
        ).prefetch_related("variants", "images", "tags").first()

        if not product:
            return {"success": False, "error": "Product not found."}

        variants = [
            {
                "id": v.pk,
                "sku": v.sku,
                "price": float(v.price),
                "stock": v.stock,
                "in_stock": v.is_in_stock,
                "attributes": str(v),
            }
            for v in product.variants.filter(is_active=True)[:10]
        ]

        return {
            "success": True,
            "product": {
                "id": product.pk,
                "title": product.title,
                "description": product.description[:600],
                "base_price": float(product.base_price),
                "compare_price": float(product.compare_price) if product.compare_price else None,
                "discount_percentage": product.discount_percentage,
                "average_rating": float(product.average_rating),
                "total_reviews": product.total_reviews,
                "category": product.category.name,
                "brand": product.brand.name if product.brand else None,
                "store": product.store.name,
                "in_stock": product.in_stock,
                "variants": variants,
                "tags": list(product.tags.values_list("name", flat=True)[:10]),
                "url": f"/products/{product.slug}/",
            },
        }

    except Exception as exc:
        logger.error("get_product_details error: %s", exc)
        return {"success": False, "error": str(exc)}


def compare_products(product_ids: list[int]) -> dict[str, Any]:
    """
    Compare multiple products side-by-side with their key attributes,
    prices, ratings, and specifications.

    Args:
        product_ids: List of product IDs to compare (max 4).
    """
    from apps.products.models import Product

    product_ids = product_ids[:4]  # Hard limit

    try:
        products = Product.objects.filter(
            pk__in=product_ids, status="APPROVED"
        ).select_related("store", "category", "brand").prefetch_related("variants")

        comparison = []
        for product in products:
            min_price = min(
                (float(v.price) for v in product.variants.filter(is_active=True)),
                default=float(product.base_price),
            )
            comparison.append({
                "id": product.pk,
                "title": product.title,
                "price_from": min_price,
                "rating": float(product.average_rating),
                "reviews": product.total_reviews,
                "in_stock": product.in_stock,
                "brand": product.brand.name if product.brand else "N/A",
                "store": product.store.name,
                "url": f"/products/{product.slug}/",
            })

        return {
            "success": True,
            "comparison": comparison,
            "recommendation": _pick_best_product(comparison),
        }

    except Exception as exc:
        logger.error("compare_products error: %s", exc)
        return {"success": False, "error": str(exc)}


def _pick_best_product(comparison: list[dict]) -> str:
    """Simple heuristic to recommend the best product from a comparison."""
    if not comparison:
        return ""
    # Score = rating * 0.6 + (1 / price_from normalized) * 0.4
    try:
        max_price = max(p["price_from"] for p in comparison if p["price_from"] > 0)
        scored = []
        for p in comparison:
            price_score = 1 - (p["price_from"] / max_price) if max_price > 0 else 0
            total = (p["rating"] / 5.0) * 0.6 + price_score * 0.4
            scored.append((total, p["title"]))
        scored.sort(reverse=True)
        return f"Based on rating and value, '{scored[0][1]}' appears to be the best choice."
    except Exception:
        return ""


def get_cart_summary(user_id: int) -> dict[str, Any]:
    """
    Retrieve the current cart contents, totals, and any potential issues
    such as out-of-stock items.

    Args:
        user_id: The integer ID of the authenticated user.
    """
    from apps.cart.models import Cart
    from apps.cart.services import CartService

    try:
        cart = Cart.objects.filter(user_id=user_id).first()
        if not cart:
            return {"success": True, "cart": {"items": [], "subtotal": 0, "total_items": 0}}

        items = CartService.get_active_items(cart)
        stock_errors = CartService.validate_stock(cart)

        item_list = [
            {
                "id": item.pk,
                "product": item.variant.product.title,
                "variant": str(item.variant),
                "quantity": item.quantity,
                "unit_price": float(item.variant.price),
                "line_total": float(item.line_total),
                "in_stock": item.variant.is_in_stock,
            }
            for item in items
        ]

        return {
            "success": True,
            "cart": {
                "items": item_list,
                "subtotal": float(CartService.calculate_subtotal(cart)),
                "total_items": cart.total_items,
                "stock_issues": stock_errors,
            },
        }

    except Exception as exc:
        logger.error("get_cart_summary error: %s", exc)
        return {"success": False, "error": str(exc)}


def get_coupon_recommendations(user_id: int, cart_total: float) -> dict[str, Any]:
    """
    Recommend applicable coupons for the user's current cart.

    Args:
        user_id: The authenticated user's ID.
        cart_total: Current cart subtotal in rupees.
    """
    from decimal import Decimal

    from apps.coupons.models import Coupon
    from apps.coupons.services import CouponService
    from django.utils import timezone

    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(pk=user_id)

        now = timezone.now()
        eligible_coupons = Coupon.objects.filter(
            is_active=True,
            valid_from__lte=now,
            valid_to__gte=now,
            min_order_amount__lte=Decimal(str(cart_total)),
        ).order_by("-discount_value")[:5]

        recommendations = []
        for coupon in eligible_coupons:
            _, error = CouponService.validate_coupon(
                coupon.code, user, Decimal(str(cart_total))
            )
            if not error:
                discount = CouponService.calculate_discount(coupon, Decimal(str(cart_total)))
                recommendations.append({
                    "code": coupon.code,
                    "type": coupon.discount_type,
                    "value": float(coupon.discount_value),
                    "savings": float(discount),
                    "description": coupon.description or f"{coupon.discount_value}{'%' if coupon.discount_type == 'PERCENTAGE' else '₹'} off",
                })

        return {
            "success": True,
            "recommendations": recommendations,
            "best_coupon": recommendations[0]["code"] if recommendations else None,
        }

    except Exception as exc:
        logger.error("get_coupon_recommendations error: %s", exc)
        return {"success": False, "error": str(exc), "recommendations": []}


def get_order_status(order_number: str, user_id: int) -> dict[str, Any]:
    """
    Get the current status and timeline of a specific order.

    Args:
        order_number: The order number string (e.g. 'SS-ABC123').
        user_id: The authenticated user's ID (for authorization).
    """
    from apps.orders.models import Order

    try:
        order = Order.objects.filter(
            order_number=order_number, user_id=user_id
        ).prefetch_related("items__variant__product", "status_history").first()

        if not order:
            return {"success": False, "error": "Order not found."}

        timeline = [
            {
                "status": h.status,
                "notes": h.notes,
                "timestamp": h.created_at.isoformat(),
            }
            for h in order.status_history.order_by("created_at")
        ]

        items = [
            {
                "product": item.variant.product.title,
                "quantity": item.quantity,
                "price": float(item.price),
                "total": float(item.total),
            }
            for item in order.items.all()
        ]

        return {
            "success": True,
            "order": {
                "order_number": order.order_number,
                "status": order.status,
                "status_display": order.get_status_display(),
                "total": float(order.total),
                "payment_method": order.payment_method,
                "created_at": order.created_at.isoformat(),
                "items": items,
                "timeline": timeline,
                "estimated_delivery": _estimate_delivery(order),
            },
        }

    except Exception as exc:
        logger.error("get_order_status error: %s", exc)
        return {"success": False, "error": str(exc)}


def _estimate_delivery(order: Any) -> str:
    """Rough delivery estimate based on shipping method and status."""
    from django.utils import timezone
    import datetime

    if order.status in ("DELIVERED", "CANCELLED", "RETURNED"):
        return order.get_status_display()

    days = 5 if order.shipping_method == "STANDARD" else 2
    eta = order.created_at + datetime.timedelta(days=days)
    if eta < timezone.now():
        return "Expected soon"
    return f"Expected by {eta.strftime('%d %b %Y')}"


def track_shipment(order_number: str) -> dict[str, Any]:
    """
    Get shipment tracking information for an order.

    Args:
        order_number: The order number to track.
    """
    from apps.orders.models import Order

    try:
        order = Order.objects.filter(order_number=order_number).first()
        if not order:
            return {"success": False, "error": "Order not found."}

        return {
            "success": True,
            "tracking": {
                "order_number": order_number,
                "status": order.status,
                "shipping_method": order.shipping_method,
                "estimated_delivery": _estimate_delivery(order),
                "last_update": order.updated_at.isoformat() if hasattr(order, "updated_at") else "",
            },
        }

    except Exception as exc:
        logger.error("track_shipment error: %s", exc)
        return {"success": False, "error": str(exc)}
