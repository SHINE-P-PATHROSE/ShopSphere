"""
AI Agent Models.

Stores conversation sessions, messages, tool call logs, vector document
metadata, and AI-generated content records — all production-grade with
full audit trail.
"""
from __future__ import annotations

import uuid
from typing import Any

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel

User = get_user_model()


class AgentType(models.TextChoices):
    CUSTOMER = "CUSTOMER", "Customer Agent"
    VENDOR = "VENDOR", "Vendor Agent"
    ADMIN = "ADMIN", "Admin Agent"


class MessageRole(models.TextChoices):
    USER = "user", "User"
    ASSISTANT = "assistant", "Assistant"
    SYSTEM = "system", "System"
    TOOL = "tool", "Tool"


# ---------------------------------------------------------------------------
# Conversation Session
# ---------------------------------------------------------------------------

class ConversationSession(TimeStampedModel):
    """
    Persistent conversation session tied to a user and agent type.
    Redis stores the hot/active window; this table is the durable log.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="ai_sessions",
        null=True,
        blank=True,
        help_text="Null for anonymous/guest sessions.",
    )
    agent_type = models.CharField(
        max_length=20,
        choices=AgentType.choices,
        default=AgentType.CUSTOMER,
        db_index=True,
    )
    session_key = models.CharField(
        max_length=64,
        db_index=True,
        help_text="Browser session key for anonymous users.",
        blank=True,
    )
    title = models.CharField(
        max_length=255,
        blank=True,
        help_text="Auto-generated from first user message.",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Arbitrary context: cart_id, order_id, vendor_id, etc.",
    )
    total_tokens_used = models.PositiveIntegerField(default=0)
    last_active_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-last_active_at"]
        indexes = [
            models.Index(fields=["user", "agent_type", "is_active"]),
            models.Index(fields=["session_key"]),
        ]
        verbose_name = "Conversation Session"

    def __str__(self) -> str:
        owner = self.user.email if self.user else f"anon:{self.session_key[:8]}"
        return f"[{self.agent_type}] {owner} — {self.title or str(self.id)[:8]}"

    def touch(self) -> None:
        """Update last_active_at without triggering full model save."""
        ConversationSession.objects.filter(pk=self.pk).update(
            last_active_at=timezone.now()
        )


class ConversationMessage(TimeStampedModel):
    """Single message in a conversation, stored permanently."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        ConversationSession,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=20, choices=MessageRole.choices, db_index=True)
    content = models.TextField()
    tool_calls = models.JSONField(
        default=list,
        blank=True,
        help_text="List of tool calls made in this message.",
    )
    tool_call_id = models.CharField(
        max_length=128,
        blank=True,
        help_text="Used for tool result messages.",
    )
    tokens_used = models.PositiveIntegerField(default=0)
    model_name = models.CharField(max_length=100, blank=True)
    latency_ms = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["session", "role"]),
        ]
        verbose_name = "Conversation Message"

    def __str__(self) -> str:
        return f"[{self.role}] {self.content[:80]}"


# ---------------------------------------------------------------------------
# Tool Call Log
# ---------------------------------------------------------------------------

class ToolCallLog(TimeStampedModel):
    """Audit log for every tool invocation by an agent."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        ConversationSession,
        on_delete=models.CASCADE,
        related_name="tool_logs",
    )
    message = models.ForeignKey(
        ConversationMessage,
        on_delete=models.CASCADE,
        related_name="tool_logs",
        null=True,
        blank=True,
    )
    tool_name = models.CharField(max_length=100, db_index=True)
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict)
    success = models.BooleanField(default=True, db_index=True)
    error_message = models.TextField(blank=True)
    latency_ms = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tool_name", "success"]),
            models.Index(fields=["session", "created_at"]),
        ]
        verbose_name = "Tool Call Log"

    def __str__(self) -> str:
        status = "✓" if self.success else "✗"
        return f"{status} {self.tool_name} ({self.latency_ms}ms)"


# ---------------------------------------------------------------------------
# Vector Document Index (metadata only — vectors live in ChromaDB/Qdrant)
# ---------------------------------------------------------------------------

class VectorDocument(TimeStampedModel):
    """
    Tracks which objects have been embedded and indexed in the vector store.
    The actual vectors live in ChromaDB/Qdrant; this is the metadata mirror.
    """

    CONTENT_TYPE_CHOICES = [
        ("product", "Product"),
        ("review", "Review"),
        ("faq", "FAQ"),
        ("cms_page", "CMS Page"),
        ("order", "Order"),
        ("support_ticket", "Support Ticket"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_type = models.CharField(
        max_length=30, choices=CONTENT_TYPE_CHOICES, db_index=True
    )
    object_id = models.CharField(max_length=255, db_index=True)
    collection_name = models.CharField(
        max_length=100,
        default="shopsphere_products",
        db_index=True,
    )
    chunk_index = models.PositiveSmallIntegerField(
        default=0,
        help_text="For long documents split into chunks.",
    )
    text_preview = models.TextField(
        max_length=500,
        blank=True,
        help_text="First 500 chars of embedded text for debugging.",
    )
    embedding_model = models.CharField(max_length=100, blank=True)
    is_indexed = models.BooleanField(default=False, db_index=True)
    indexed_at = models.DateTimeField(null=True, blank=True)
    checksum = models.CharField(
        max_length=64,
        blank=True,
        help_text="SHA-256 of embedded text to detect stale embeddings.",
    )

    class Meta:
        unique_together = ["content_type", "object_id", "chunk_index"]
        indexes = [
            models.Index(fields=["content_type", "is_indexed"]),
            models.Index(fields=["collection_name"]),
        ]
        verbose_name = "Vector Document"

    def __str__(self) -> str:
        return f"{self.content_type}:{self.object_id}[{self.chunk_index}]"


# ---------------------------------------------------------------------------
# AI-Generated Content
# ---------------------------------------------------------------------------

class AIGeneratedContent(TimeStampedModel):
    """
    Stores AI-generated content (product descriptions, SEO meta, emails, etc.)
    with full audit trail, so vendors/admins can approve before publishing.
    """

    CONTENT_TYPE_CHOICES = [
        ("product_title", "Product Title"),
        ("product_description", "Product Description"),
        ("seo_meta", "SEO Meta"),
        ("tags", "Product Tags"),
        ("email_content", "Email Content"),
        ("marketing_copy", "Marketing Copy"),
        ("review_summary", "Review Summary"),
        ("support_reply", "Support Reply"),
        ("pricing_suggestion", "Pricing Suggestion"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("published", "Published"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_type = models.CharField(
        max_length=30, choices=CONTENT_TYPE_CHOICES, db_index=True
    )
    object_id = models.CharField(max_length=255, db_index=True)
    generated_content = models.TextField()
    original_content = models.TextField(
        blank=True,
        help_text="Content before AI generation (for comparison).",
    )
    prompt_used = models.TextField(blank=True)
    model_name = models.CharField(max_length=100, blank=True)
    tokens_used = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True
    )
    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_generated_content",
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_reviewed_content",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    feedback = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["status"]),
        ]
        verbose_name = "AI Generated Content"

    def __str__(self) -> str:
        return f"{self.content_type} for {self.object_id} [{self.status}]"


# ---------------------------------------------------------------------------
# AI Insight (analytics summaries, fraud flags, forecasts)
# ---------------------------------------------------------------------------

class AIInsight(TimeStampedModel):
    """
    Stores periodically-generated AI insights (revenue analysis, fraud
    detection signals, inventory forecasts, sentiment summaries, etc.)
    """

    INSIGHT_TYPE_CHOICES = [
        ("revenue_analysis", "Revenue Analysis"),
        ("fraud_signal", "Fraud Signal"),
        ("inventory_forecast", "Inventory Forecast"),
        ("sentiment_summary", "Customer Sentiment Summary"),
        ("sales_prediction", "Sales Prediction"),
        ("daily_summary", "Daily Business Summary"),
        ("customer_segment", "Customer Segmentation"),
        ("churn_risk", "Churn Risk"),
    ]

    SEVERITY_CHOICES = [
        ("info", "Info"),
        ("warning", "Warning"),
        ("critical", "Critical"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    insight_type = models.CharField(
        max_length=30, choices=INSIGHT_TYPE_CHOICES, db_index=True
    )
    title = models.CharField(max_length=255)
    summary = models.TextField()
    data = models.JSONField(
        default=dict,
        help_text="Structured data supporting this insight.",
    )
    severity = models.CharField(
        max_length=10, choices=SEVERITY_CHOICES, default="info", db_index=True
    )
    related_object_type = models.CharField(max_length=50, blank=True)
    related_object_id = models.CharField(max_length=255, blank=True)
    is_acknowledged = models.BooleanField(default=False, db_index=True)
    acknowledged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="acknowledged_insights",
    )
    model_name = models.CharField(max_length=100, blank=True)
    confidence_score = models.FloatField(
        default=0.0,
        help_text="Model confidence 0.0–1.0.",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["insight_type", "severity"]),
            models.Index(fields=["is_acknowledged"]),
        ]
        verbose_name = "AI Insight"

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.title}"
