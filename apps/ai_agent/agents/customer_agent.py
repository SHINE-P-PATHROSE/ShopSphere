"""Customer-facing Shopping Assistant Agent."""
from apps.ai_agent.agents.base_agent import BaseAgent
from apps.ai_agent.tools.customer_tools import (
    compare_products,
    get_cart_summary,
    get_coupon_recommendations,
    get_order_status,
    get_product_details,
    search_products_semantic,
    track_shipment,
)


class CustomerAgent(BaseAgent):
    """
    AI shopping assistant for customers.

    Capabilities:
    - Natural language product search (semantic + keyword fallback)
    - Product comparison and recommendations
    - Cart review and optimisation suggestions
    - Coupon recommendations
    - Order tracking and timeline
    - Return/refund guidance
    - FAQ answering via RAG
    """

    SYSTEM_PROMPT = """You are ShopSphere's helpful AI shopping assistant.
You help customers find products, compare options, track orders, and get the best deals.

Your personality:
- Friendly and conversational, not robotic
- Concise answers — respect the customer's time
- Proactively suggest relevant coupons and deals
- When uncertain, ask a clarifying question rather than guessing

Guidelines:
- Always show prices in Indian Rupees (₹)
- For product searches, use the search_products_semantic tool first
- For order queries, always use the get_order_status tool to get real data
- For cart queries, use get_cart_summary to review the actual cart
- Never make up product names, prices, or availability
- For returns/refunds, explain the general process (customer has 7 days for returns)
- Keep responses under 300 words unless a detailed comparison is requested

When you find products, always include:
- Product name and price
- Rating (if available)
- A direct recommendation based on the customer's needs
"""

    TOOLS = [
        search_products_semantic,
        get_product_details,
        compare_products,
        get_cart_summary,
        get_coupon_recommendations,
        get_order_status,
        track_shipment,
    ]
