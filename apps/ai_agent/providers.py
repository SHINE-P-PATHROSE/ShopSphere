"""
LLM Provider Abstraction Layer.

Architectural decision: All LLM calls go through `get_llm_client()`.
Switching providers (OpenAI → Gemini → Claude → DeepSeek) requires only
an env var change — zero code changes.

Supported providers:
  - openai      (GPT-4o, GPT-4-turbo, GPT-3.5-turbo)
  - gemini      (gemini-1.5-pro, gemini-1.5-flash)
  - anthropic   (claude-3-5-sonnet, claude-3-haiku)
  - deepseek    (deepseek-chat, deepseek-coder)
  - ollama      (any local model via Ollama API)

Each provider is wrapped in a unified LangChain ChatModel interface so
LangGraph agents are fully provider-agnostic.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)


def get_llm_client(
    provider: str | None = None,
    model: str | None = None,
    temperature: float | None = None,
    streaming: bool = False,
    **kwargs: Any,
) -> Any:
    """
    Return a LangChain-compatible chat model for the given provider.

    Falls back to AI_PROVIDER / AI_MODEL env vars if not specified.
    Raises ImportError with a helpful message if required package is missing.
    """
    provider = provider or getattr(settings, "AI_PROVIDER", "openai")
    temperature = temperature if temperature is not None else getattr(
        settings, "AI_TEMPERATURE", 0.2
    )

    provider = provider.lower()

    if provider == "openai":
        return _get_openai(model, temperature, streaming, **kwargs)
    elif provider == "gemini":
        return _get_gemini(model, temperature, streaming, **kwargs)
    elif provider == "anthropic":
        return _get_anthropic(model, temperature, streaming, **kwargs)
    elif provider == "deepseek":
        return _get_deepseek(model, temperature, streaming, **kwargs)
    elif provider == "ollama":
        return _get_ollama(model, temperature, streaming, **kwargs)
    else:
        raise ValueError(
            f"Unknown AI provider: '{provider}'. "
            "Valid choices: openai, gemini, anthropic, deepseek, ollama"
        )


def _get_openai(model: str | None, temperature: float, streaming: bool, **kwargs: Any) -> Any:
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        raise ImportError("Run: pip install langchain-openai")

    api_key = getattr(settings, "OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not configured.")

    return ChatOpenAI(
        model=model or getattr(settings, "AI_MODEL", "gpt-4o-mini"),
        temperature=temperature,
        streaming=streaming,
        api_key=api_key,
        **kwargs,
    )


def _get_gemini(model: str | None, temperature: float, streaming: bool, **kwargs: Any) -> Any:
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError:
        raise ImportError("Run: pip install langchain-google-genai")

    api_key = getattr(settings, "GOOGLE_API_KEY", "")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is not configured.")

    return ChatGoogleGenerativeAI(
        model=model or getattr(settings, "AI_MODEL", "gemini-1.5-flash"),
        temperature=temperature,
        google_api_key=api_key,
        **kwargs,
    )


def _get_anthropic(model: str | None, temperature: float, streaming: bool, **kwargs: Any) -> Any:
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError:
        raise ImportError("Run: pip install langchain-anthropic")

    api_key = getattr(settings, "ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is not configured.")

    return ChatAnthropic(
        model=model or getattr(settings, "AI_MODEL", "claude-3-5-sonnet-20241022"),
        temperature=temperature,
        api_key=api_key,
        **kwargs,
    )


def _get_deepseek(model: str | None, temperature: float, streaming: bool, **kwargs: Any) -> Any:
    """DeepSeek uses the OpenAI-compatible API."""
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        raise ImportError("Run: pip install langchain-openai")

    api_key = getattr(settings, "DEEPSEEK_API_KEY", "")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY is not configured.")

    return ChatOpenAI(
        model=model or getattr(settings, "AI_MODEL", "deepseek-chat"),
        temperature=temperature,
        streaming=streaming,
        api_key=api_key,
        base_url="https://api.deepseek.com/v1",
        **kwargs,
    )


def _get_ollama(model: str | None, temperature: float, streaming: bool, **kwargs: Any) -> Any:
    try:
        from langchain_ollama import ChatOllama
    except ImportError:
        raise ImportError("Run: pip install langchain-ollama")

    base_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
    return ChatOllama(
        model=model or getattr(settings, "AI_MODEL", "llama3.2"),
        temperature=temperature,
        base_url=base_url,
        **kwargs,
    )


def get_embeddings_client(provider: str | None = None) -> Any:
    """
    Return a LangChain-compatible embeddings model.
    Uses AI_EMBEDDINGS_PROVIDER env var (defaults to openai).
    """
    provider = provider or getattr(settings, "AI_EMBEDDINGS_PROVIDER", "openai")
    provider = provider.lower()

    if provider == "openai":
        try:
            from langchain_openai import OpenAIEmbeddings
        except ImportError:
            raise ImportError("Run: pip install langchain-openai")
        return OpenAIEmbeddings(
            model=getattr(settings, "AI_EMBEDDINGS_MODEL", "text-embedding-3-small"),
            api_key=getattr(settings, "OPENAI_API_KEY", ""),
        )
    elif provider == "gemini":
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
        except ImportError:
            raise ImportError("Run: pip install langchain-google-genai")
        return GoogleGenerativeAIEmbeddings(
            model=getattr(settings, "AI_EMBEDDINGS_MODEL", "models/embedding-001"),
            google_api_key=getattr(settings, "GOOGLE_API_KEY", ""),
        )
    elif provider == "ollama":
        try:
            from langchain_ollama import OllamaEmbeddings
        except ImportError:
            raise ImportError("Run: pip install langchain-ollama")
        return OllamaEmbeddings(
            model=getattr(settings, "AI_EMBEDDINGS_MODEL", "nomic-embed-text"),
            base_url=getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434"),
        )
    else:
        raise ValueError(f"Unknown embeddings provider: '{provider}'")
