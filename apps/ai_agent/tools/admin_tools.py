"""
Admin Agent Tools.

Provides business intelligence, fraud detection, inventory forecasting,
sentiment analysis, and daily business summaries for platform administrators.
"""
from __future__ import annotations

import logging
from datetime import timedelta
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)


def _llm_generate(prompt: str, max_tokens: int = 1024) -> str:
    from apps.ai_agent.providers import get_llm_client
    from langchain_core.messages import HumanMessage
    llm = get_llm_client()
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()


def get_revenue_analysis(days: int = 30) -> dict[str, Any]:
    """
    Generate a comprehensive revenue analysis for the platform.

    Args:
        days: Analysis period in days (default 30).
    """
    from django.db.models import Avg, Count, Sum
    from django.utils import timezone

    from apps.accounts.models import User
    from apps.analytics.services import AnalyticsService
    from apps.orders.models import Order

    try:
        data = AnalyticsService.admin_dashboard(days)

        since = timezone.now() - timedelta(days=days)
        prev_since = since - timedelta(days=days)

        # Compare to previous period
        prev_orders = Order.objects.filter(
            created_at__gte=prev_since,
            created_at__lt=since,
        ).exclude(status="CANCELLED")
        prev_revenue = prev_orders.aggregate(total=Sum("total"))["total"] or Decimal("0")
        prev_count = prev_orders.count()

        current_revenue = data["total_revenue"]
        current_count = data["total_orders"]

        revenue_change = float(
            (current_revenue - prev_revenue) / prev_revenue * 100
            if prev_revenue > 0
            else 0
        )
        order_change = float(
            (current_count - prev_count) / prev_count * 100
            if prev_count > 0
            else 0
        )

        return {
            "success": True,
            "period_days": days,
            "current_period": {
                "revenue": float(current_revenue),
                "orders": current_count,
                "avg_order_value": float(data["avg_order_value"]),
                "new_customers": data["new_customers"],
                "new_vendors": data["new_vendors"],
            },
            "previous_period": {
                "revenue": float(prev_revenue),
                "orders": prev_count,
            },
            "growth": {
                "revenue_change_pct": round(revenue_change, 2),
                "order_change_pct": round(order_change, 2),
            },
            "orders_by_status": data["orders_by_status"],
            "top_products": [
                {
                    "title": p.title,
                    "sales_count": p.sales_count,
                }
                for p in data["top_products"][:5]
            ],
        }

    except Exception as exc:
        logger.error("get_revenue_analysis error: %s", exc)
        return {"success": False, "error": str(exc)}


def detect_fraud_signals(days: int = 7) -> dict[str, Any]:
    """
    Detect potential fraud patterns: multiple orders from same IP,
    unusual return rates, high cancellation users, etc.

    Args:
        days: Lookback period for fraud detection.
    """
    from django.db.models import Avg, Count, Q
    from django.utils import timezone

    from apps.orders.models import Order, ReturnRequest

    try:
        since = timezone.now() - timedelta(days=days)

        # Users with abnormally high cancellation rates
        high_cancellations = (
            Order.objects.filter(created_at__gte=since)
            .values("user")
            .annotate(
                total=Count("id"),
                cancelled=Count("id", filter=Q(status="CANCELLED")),
            )
            .filter(total__gte=3, cancelled__gte=2)
            .order_by("-cancelled")[:10]
        )

        # High return rates
        high_returns = (
            ReturnRequest.objects.filter(created_at__gte=since)
            .values("order_item__order__user")
            .annotate(count=Count("id"))
            .filter(count__gte=2)
            .order_by("-count")[:10]
        )

        # Orders with suspicious patterns
        guest_orders_high = Order.objects.filter(
            created_at__gte=since,
            is_guest=True,
            total__gte=10000,
        ).count()

        signals = []
        if high_cancellations:
            signals.append({
                "type": "HIGH_CANCELLATION_RATE",
                "severity": "warning",
                "count": len(list(high_cancellations)),
                "description": "Users with >50% cancellation rate in period",
            })
        if high_returns:
            signals.append({
                "type": "HIGH_RETURN_RATE",
                "severity": "warning",
                "count": len(list(high_returns)),
                "description": "Users with 2+ returns in period",
            })
        if guest_orders_high > 10:
            signals.append({
                "type": "HIGH_VALUE_GUEST_ORDERS",
                "severity": "info",
                "count": guest_orders_high,
                "description": f"{guest_orders_high} high-value guest orders (>₹10,000)",
            })

        return {
            "success": True,
            "period_days": days,
            "fraud_signals": signals,
            "risk_level": "high" if any(s["severity"] == "critical" for s in signals)
            else "medium" if signals
            else "low",
        }

    except Exception as exc:
        logger.error("detect_fraud_signals error: %s", exc)
        return {"success": False, "error": str(exc)}


def forecast_inventory(days_ahead: int = 14) -> dict[str, Any]:
    """
    Forecast which products will run out of stock in the next N days
    based on recent sales velocity.

    Args:
        days_ahead: How many days ahead to forecast.
    """
    from django.db.models import Sum
    from django.utils import timezone

    from apps.orders.models import OrderItem
    from apps.products.models import ProductVariant

    try:
        lookback = 30
        since = timezone.now() - timedelta(days=lookback)

        sales_data = (
            OrderItem.objects.filter(created_at__gte=since)
            .exclude(order__status="CANCELLED")
            .values("variant_id")
            .annotate(units_sold=Sum("quantity"))
        )
        sales_map = {s["variant_id"]: s["units_sold"] for s in sales_data}

        stockout_risks = []
        variants = ProductVariant.objects.filter(
            is_active=True, stock__gt=0
        ).select_related("product", "product__store")[:500]

        for v in variants:
            sold = sales_map.get(v.pk, 0)
            if sold == 0:
                continue
            daily_velocity = sold / lookback
            days_until_stockout = int(v.stock / daily_velocity)

            if days_until_stockout <= days_ahead:
                stockout_risks.append({
                    "sku": v.sku,
                    "product": v.product.title,
                    "store": v.product.store.name,
                    "current_stock": v.stock,
                    "daily_velocity": round(daily_velocity, 2),
                    "days_until_stockout": days_until_stockout,
                    "reorder_quantity_suggested": int(daily_velocity * 30),
                })

        stockout_risks.sort(key=lambda x: x["days_until_stockout"])

        return {
            "success": True,
            "forecast_days": days_ahead,
            "at_risk_count": len(stockout_risks),
            "at_risk_items": stockout_risks[:20],
        }

    except Exception as exc:
        logger.error("forecast_inventory error: %s", exc)
        return {"success": False, "error": str(exc)}


def get_sentiment_summary(days: int = 7) -> dict[str, Any]:
    """
    Analyse customer review sentiment across the platform using AI.

    Args:
        days: Lookback period for reviews to analyse.
    """
    from django.utils import timezone

    from apps.reviews.models import Review

    try:
        since = timezone.now() - timedelta(days=days)
        reviews = Review.objects.filter(
            created_at__gte=since, is_approved=True
        ).values("rating", "title", "body")[:50]

        if not reviews:
            return {
                "success": True,
                "summary": "No reviews in this period.",
                "sentiment": "neutral",
                "avg_rating": 0,
                "review_count": 0,
            }

        review_list = list(reviews)
        avg_rating = sum(r["rating"] for r in review_list) / len(review_list)
        positive = sum(1 for r in review_list if r["rating"] >= 4)
        negative = sum(1 for r in review_list if r["rating"] <= 2)

        # Use LLM for qualitative summary
        sample_texts = "\n".join(
            f"[{r['rating']}★] {r['title']}: {r['body'][:150]}"
            for r in review_list[:15]
        )

        prompt = (
            f"Summarise customer sentiment from these {len(review_list)} recent reviews "
            f"on an Indian e-commerce platform.\n\n"
            f"{sample_texts}\n\n"
            "Provide:\n"
            "1. Overall sentiment (1 sentence)\n"
            "2. Top 3 things customers love\n"
            "3. Top 3 areas for improvement\n"
            "4. Actionable recommendation for the business\n\n"
            "Be concise and data-driven."
        )

        ai_summary = _llm_generate(prompt, max_tokens=400)

        return {
            "success": True,
            "period_days": days,
            "review_count": len(review_list),
            "avg_rating": round(avg_rating, 2),
            "positive_count": positive,
            "negative_count": negative,
            "sentiment": "positive" if avg_rating >= 3.5 else "mixed" if avg_rating >= 2.5 else "negative",
            "ai_summary": ai_summary,
        }

    except Exception as exc:
        logger.error("get_sentiment_summary error: %s", exc)
        return {"success": False, "error": str(exc)}


def generate_daily_summary(date_str: str = "") -> dict[str, Any]:
    """
    Generate an AI-written daily business summary for the admin dashboard.

    Args:
        date_str: Optional date string YYYY-MM-DD. Defaults to yesterday.
    """
    import datetime

    from apps.analytics.services import AnalyticsService

    try:
        if date_str:
            target_date = datetime.date.fromisoformat(date_str)
        else:
            target_date = datetime.date.today() - datetime.timedelta(days=1)

        data = AnalyticsService.admin_dashboard(1)

        prompt = (
            f"Write a concise daily business summary for {target_date.strftime('%d %B %Y')} "
            f"for a multi-vendor Indian e-commerce platform called ShopSphere.\n\n"
            f"Key Metrics:\n"
            f"- Orders: {data['total_orders']}\n"
            f"- Revenue: ₹{data['total_revenue']:,.2f}\n"
            f"- Avg Order Value: ₹{data['avg_order_value']:,.2f}\n"
            f"- New Customers: {data['new_customers']}\n"
            f"- New Vendors: {data['new_vendors']}\n"
            f"- Pending Vendor Approvals: {data['pending_vendors']}\n\n"
            "Write a 3-paragraph executive summary covering:\n"
            "1. Performance highlights\n"
            "2. Areas of concern\n"
            "3. Recommended actions for today\n\n"
            "Use a professional, data-driven tone. Keep it under 200 words."
        )

        summary = _llm_generate(prompt, max_tokens=500)

        return {
            "success": True,
            "date": target_date.isoformat(),
            "metrics": {
                "orders": data["total_orders"],
                "revenue": float(data["total_revenue"]),
                "avg_order_value": float(data["avg_order_value"]),
                "new_customers": data["new_customers"],
            },
            "ai_summary": summary,
        }

    except Exception as exc:
        logger.error("generate_daily_summary error: %s", exc)
        return {"success": False, "error": str(exc)}
