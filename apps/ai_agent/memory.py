"""
Conversation Memory Management.

Architectural decision: Two-tier memory:
  1. Redis (hot tier) — last N messages for active conversations, TTL-expiring.
  2. PostgreSQL (cold tier) — permanent message log via ConversationMessage model.

This gives us sub-millisecond context retrieval during active sessions while
maintaining a full audit trail in the database.
"""
from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

from django.conf import settings
from django.core.cache import cache

from apps.ai_agent.models import ConversationMessage, ConversationSession, MessageRole

logger = logging.getLogger(__name__)

# Redis key format: ai:memory:{session_id}
_MEMORY_KEY = "ai:memory:{session_id}"
# Keep last 20 messages in Redis; configurable via settings
_WINDOW_SIZE = getattr(settings, "AI_MEMORY_WINDOW_SIZE", 20)
# TTL: 2 hours for active sessions
_MEMORY_TTL = getattr(settings, "AI_MEMORY_TTL_SECONDS", 7200)


def get_memory_key(session_id: str | UUID) -> str:
    return _MEMORY_KEY.format(session_id=str(session_id))


def load_memory(session_id: str | UUID) -> list[dict[str, Any]]:
    """
    Load conversation history for an active session.
    Tries Redis first; falls back to database if cache miss.
    """
    key = get_memory_key(session_id)
    cached = cache.get(key)

    if cached is not None:
        return cached  # type: ignore[return-value]

    # Cache miss — rebuild from DB
    messages = list(
        ConversationMessage.objects.filter(
            session_id=session_id,
            role__in=[MessageRole.USER, MessageRole.ASSISTANT, MessageRole.TOOL],
        )
        .order_by("-created_at")[: _WINDOW_SIZE]
        .values("role", "content", "tool_calls", "tool_call_id")
    )
    messages.reverse()  # oldest first

    serializable = [
        {
            "role": m["role"],
            "content": m["content"],
            "tool_calls": m["tool_calls"],
            "tool_call_id": m["tool_call_id"],
        }
        for m in messages
    ]

    # Populate Redis
    cache.set(key, serializable, timeout=_MEMORY_TTL)
    return serializable


def append_to_memory(
    session_id: str | UUID,
    role: str,
    content: str,
    tool_calls: list | None = None,
    tool_call_id: str = "",
) -> None:
    """
    Append a new message to both Redis and the database.
    Maintains a sliding window in Redis.
    """
    # 1. Persist to DB
    try:
        ConversationMessage.objects.create(
            session_id=session_id,
            role=role,
            content=content,
            tool_calls=tool_calls or [],
            tool_call_id=tool_call_id,
        )
    except Exception as exc:
        logger.error("Failed to persist message to DB: %s", exc)

    # 2. Update Redis window
    key = get_memory_key(session_id)
    history: list = cache.get(key) or []
    history.append(
        {
            "role": role,
            "content": content,
            "tool_calls": tool_calls or [],
            "tool_call_id": tool_call_id,
        }
    )
    # Trim to window size
    if len(history) > _WINDOW_SIZE:
        history = history[-_WINDOW_SIZE:]

    cache.set(key, history, timeout=_MEMORY_TTL)

    # 3. Touch session last_active_at
    try:
        ConversationSession.objects.filter(pk=session_id).update(
            last_active_at=__import__("django.utils.timezone", fromlist=["timezone"]).timezone.now()
        )
    except Exception:
        pass


def clear_memory(session_id: str | UUID) -> None:
    """Clear Redis cache for a session (DB remains)."""
    cache.delete(get_memory_key(session_id))


def build_langchain_messages(
    history: list[dict[str, Any]],
) -> list[Any]:
    """
    Convert our internal message format to LangChain message objects.
    Provider-agnostic since all LangChain chat models accept these types.
    """
    from langchain_core.messages import (
        AIMessage,
        HumanMessage,
        SystemMessage,
        ToolMessage,
    )

    result = []
    for msg in history:
        role = msg.get("role", "")
        content = msg.get("content", "")
        tool_calls = msg.get("tool_calls") or []
        tool_call_id = msg.get("tool_call_id", "")

        if role == MessageRole.USER:
            result.append(HumanMessage(content=content))
        elif role == MessageRole.ASSISTANT:
            if tool_calls:
                result.append(
                    AIMessage(content=content, tool_calls=tool_calls)
                )
            else:
                result.append(AIMessage(content=content))
        elif role == MessageRole.SYSTEM:
            result.append(SystemMessage(content=content))
        elif role == MessageRole.TOOL:
            result.append(
                ToolMessage(content=content, tool_call_id=tool_call_id)
            )

    return result
