"""AI Agent Tool Registry — all tools importable from this package."""
from apps.ai_agent.tools.customer_tools import (
    compare_products,
    get_cart_summary,
    get_coupon_recommendations,
    get_order_status,
    get_product_details,
    search_products_semantic,
    track_shipment,
)
from apps.ai_agent.tools.vendor_tools import (
    generate_product_description,
    generate_product_tags,
    generate_product_title,
    get_inventory_insights,
    get_sales_analysis,
    suggest_pricing,
)
from apps.ai_agent.tools.admin_tools import (
    detect_fraud_signals,
    forecast_inventory,
    generate_daily_summary,
    get_revenue_analysis,
    get_sentiment_summary,
)

__all__ = [
    # Customer
    "search_products_semantic",
    "get_product_details",
    "compare_products",
    "get_cart_summary",
    "get_coupon_recommendations",
    "get_order_status",
    "track_shipment",
    # Vendor
    "generate_product_title",
    "generate_product_description",
    "generate_product_tags",
    "suggest_pricing",
    "get_inventory_insights",
    "get_sales_analysis",
    # Admin
    "get_revenue_analysis",
    "detect_fraud_signals",
    "forecast_inventory",
    "get_sentiment_summary",
    "generate_daily_summary",
]
