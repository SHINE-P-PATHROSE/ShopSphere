"""
Base Agent using LangGraph ReAct pattern.

Architectural decision: All three agent types (Customer, Vendor, Admin)
share this base class. Each subclass only needs to define:
  - SYSTEM_PROMPT: str
  - TOOLS: list of callable tool functions

The base handles:
  - LangGraph ReAct loop (reason → act → observe → repeat)
  - Memory loading/saving (Redis hot tier + PostgreSQL cold tier)
  - Tool call logging (ToolCallLog model)
  - Token tracking
  - Error handling and graceful fallback

This design means switching LLM providers, adding tools, or changing
memory backends requires zero changes to this class.
"""
from __future__ import annotations

import logging
import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, Annotated, TypedDict

from django.conf import settings

from apps.ai_agent.memory import (
    append_to_memory,
    build_langchain_messages,
    load_memory,
)
from apps.ai_agent.models import (
    ConversationSession,
    MessageRole,
    ToolCallLog,
)

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    messages: list[Any]
    session_id: str


class BaseAgent(ABC):
    """
    Abstract base class for all ShopSphere AI agents.
    Subclasses provide system prompt and tool list.
    """

    SYSTEM_PROMPT: str = "You are a helpful assistant."
    TOOLS: list = []

    def __init__(self) -> None:
        self._graph = None

    def _build_graph(self) -> Any:
        """Build the LangGraph ReAct agent graph (lazy — built once per instance)."""
        try:
            from langgraph.prebuilt import create_react_agent
        except ImportError:
            raise ImportError(
                "LangGraph not installed. Run: pip install langgraph"
            )

        from apps.ai_agent.providers import get_llm_client
        from langchain_core.messages import SystemMessage

        llm = get_llm_client()

        # Bind tools to LLM if tools are defined
        if self.TOOLS:
            try:
                # Wrap plain functions as LangChain tools
                from langchain_core.tools import tool as lc_tool
                lc_tools = []
                for fn in self.TOOLS:
                    if hasattr(fn, "name"):
                        # Already a LangChain tool
                        lc_tools.append(fn)
                    else:
                        # Wrap with @tool decorator
                        wrapped = lc_tool(fn)
                        lc_tools.append(wrapped)

                return create_react_agent(
                    llm,
                    lc_tools,
                    state_modifier=SystemMessage(content=self.SYSTEM_PROMPT),
                )
            except Exception as exc:
                logger.error("Failed to build agent graph with tools: %s", exc)
                raise

        return create_react_agent(
            llm,
            [],
            state_modifier=SystemMessage(content=self.SYSTEM_PROMPT),
        )

    @property
    def graph(self) -> Any:
        """Lazy-initialise the LangGraph compiled graph."""
        if self._graph is None:
            self._graph = self._build_graph()
        return self._graph

    def chat(
        self,
        session_id: str | uuid.UUID,
        user_message: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Process a user message and return the assistant's response.

        This is the main entry point for all agent interactions.
        It handles memory loading, LangGraph invocation, memory saving,
        and full audit logging.

        Args:
            session_id: UUID of the ConversationSession.
            user_message: The user's message text.
            context: Optional extra context (user_id, cart_id, etc.)

        Returns:
            dict with keys: response, session_id, tokens_used, latency_ms
        """
        from langchain_core.messages import HumanMessage

        session_id = str(session_id)
        start_time = time.time()

        try:
            # 1. Load conversation history
            history = load_memory(session_id)
            lc_messages = build_langchain_messages(history)

            # 2. Add current user message
            lc_messages.append(HumanMessage(content=user_message))

            # 3. Persist user message
            append_to_memory(session_id, MessageRole.USER, user_message)

            # 4. Invoke the LangGraph agent
            result = self.graph.invoke({"messages": lc_messages})

            # 5. Extract final assistant response
            response_text = self._extract_final_response(result)
            tool_calls_made = self._extract_tool_calls(result)

            # 6. Calculate metrics
            latency_ms = int((time.time() - start_time) * 1000)
            tokens_used = self._count_tokens(result)

            # 7. Persist assistant response
            append_to_memory(
                session_id,
                MessageRole.ASSISTANT,
                response_text,
                tool_calls=tool_calls_made,
            )

            # 8. Log tool calls to DB
            if tool_calls_made:
                self._log_tool_calls(session_id, tool_calls_made, latency_ms)

            # 9. Update session token count
            self._update_session_tokens(session_id, tokens_used)

            # 10. Auto-title session from first message
            self._maybe_set_session_title(session_id, user_message)

            return {
                "success": True,
                "response": response_text,
                "session_id": session_id,
                "tokens_used": tokens_used,
                "latency_ms": latency_ms,
                "tool_calls_count": len(tool_calls_made),
            }

        except Exception as exc:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "Agent chat error (session=%s): %s", session_id, exc, exc_info=True
            )
            error_response = (
                "I'm having trouble processing your request right now. "
                "Please try again in a moment."
            )
            append_to_memory(session_id, MessageRole.ASSISTANT, error_response)
            return {
                "success": False,
                "response": error_response,
                "session_id": session_id,
                "tokens_used": 0,
                "latency_ms": latency_ms,
                "error": str(exc),
            }

    def _extract_final_response(self, result: dict[str, Any]) -> str:
        """Extract the last AIMessage content from LangGraph result."""
        from langchain_core.messages import AIMessage

        messages = result.get("messages", [])
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.content:
                return str(msg.content)
        return "I couldn't generate a response. Please try again."

    def _extract_tool_calls(self, result: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract all tool calls made during agent execution."""
        from langchain_core.messages import AIMessage

        tool_calls = []
        for msg in result.get("messages", []):
            if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_calls.append({
                        "tool_name": tc.get("name", ""),
                        "input": tc.get("args", {}),
                        "id": tc.get("id", ""),
                    })
        return tool_calls

    def _count_tokens(self, result: dict[str, Any]) -> int:
        """Best-effort token count from LangGraph response metadata."""
        for msg in result.get("messages", []):
            meta = getattr(msg, "response_metadata", {})
            usage = meta.get("token_usage") or meta.get("usage", {})
            if usage:
                return usage.get("total_tokens", 0)
        return 0

    def _log_tool_calls(
        self,
        session_id: str,
        tool_calls: list[dict[str, Any]],
        total_latency_ms: int,
    ) -> None:
        """Persist tool call audit records to the database."""
        try:
            logs = [
                ToolCallLog(
                    session_id=session_id,
                    tool_name=tc.get("tool_name", ""),
                    input_data=tc.get("input", {}),
                    output_data={},  # output captured separately via ToolMessage
                    success=True,
                    latency_ms=total_latency_ms // len(tool_calls) if tool_calls else 0,
                )
                for tc in tool_calls
            ]
            ToolCallLog.objects.bulk_create(logs, ignore_conflicts=True)
        except Exception as exc:
            logger.error("Failed to log tool calls: %s", exc)

    def _update_session_tokens(self, session_id: str, tokens: int) -> None:
        """Increment token counter on the session record."""
        try:
            from django.db.models import F
            ConversationSession.objects.filter(pk=session_id).update(
                total_tokens_used=F("total_tokens_used") + tokens
            )
        except Exception:
            pass

    def _maybe_set_session_title(self, session_id: str, first_message: str) -> None:
        """Set session title from first user message if not already set."""
        try:
            session = ConversationSession.objects.filter(pk=session_id, title="").first()
            if session:
                title = first_message[:80].rstrip() + ("..." if len(first_message) > 80 else "")
                ConversationSession.objects.filter(pk=session_id).update(title=title)
        except Exception:
            pass
