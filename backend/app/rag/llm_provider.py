"""
LLM provider factory.
Supports OpenAI GPT and local Ollama models, switchable via environment variable.
"""

import logging
from typing import Generator, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)

# Module-level cache
_llm_instance = None


def get_llm():
    """
    Get the configured LLM instance.

    Returns a LangChain-compatible LLM based on the ``LLM_PROVIDER`` setting.
    """
    global _llm_instance

    if _llm_instance is not None:
        return _llm_instance

    provider = settings.llm_provider.lower()
    logger.info("Initialising LLM provider: %s", provider)

    if provider == "openai":
        _llm_instance = _create_openai_llm()
    elif provider == "ollama":
        _llm_instance = _create_ollama_llm()
    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Use 'openai' or 'ollama'.")

    return _llm_instance


def _create_openai_llm():
    """Create an OpenAI ChatGPT instance."""
    try:
        from langchain_openai import ChatOpenAI

        if not settings.openai_api_key or settings.openai_api_key == "your-openai-api-key-here":
            raise ValueError("OPENAI_API_KEY is not set. Please set it in your .env file.")

        llm = ChatOpenAI(
            model=settings.openai_model,
            openai_api_key=settings.openai_api_key,
            temperature=0.3,
            max_tokens=2048,
            streaming=True,
        )
        logger.info("OpenAI LLM initialised: model=%s", settings.openai_model)
        return llm

    except ImportError:
        raise ImportError("Install langchain-openai: pip install langchain-openai")


def _create_ollama_llm():
    """Create a local Ollama LLM instance."""
    try:
        from langchain_community.chat_models import ChatOllama

        llm = ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            temperature=0.3,
            num_predict=2048,
        )
        logger.info(
            "Ollama LLM initialised: model=%s, base_url=%s",
            settings.ollama_model,
            settings.ollama_base_url,
        )
        return llm

    except ImportError:
        raise ImportError("Install langchain-community: pip install langchain-community")


def stream_llm_response(messages) -> Generator[str, None, None]:
    """
    Stream tokens from the LLM.

    Args:
        messages: The Langchain messages or prompt string.

    Yields:
        Individual tokens/chunks of the response.
    """
    llm = get_llm()

    try:
        for chunk in llm.stream(messages):
            if hasattr(chunk, "content") and chunk.content:
                yield chunk.content
            elif isinstance(chunk, str):
                yield chunk

    except Exception as exc:
        logger.error("LLM streaming error: %s", exc, exc_info=True)
        raise


def invoke_llm(messages) -> str:
    """
    Get a full (non-streaming) response from the LLM.

    Args:
        messages: The Langchain messages or prompt string.

    Returns:
        The complete response text.
    """
    llm = get_llm()

    try:
        result = llm.invoke(messages)
        if hasattr(result, "content"):
            return result.content
        return str(result)
    except Exception as exc:
        logger.error("LLM invoke error: %s", exc, exc_info=True)
        raise
