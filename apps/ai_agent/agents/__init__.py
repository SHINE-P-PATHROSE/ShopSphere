"""Agent subclasses — one per agent type."""
from apps.ai_agent.agents.customer_agent import CustomerAgent
from apps.ai_agent.agents.vendor_agent import VendorAgent
from apps.ai_agent.agents.admin_agent import AdminAgent

__all__ = ["CustomerAgent", "VendorAgent", "AdminAgent"]
