"""Core LLM module using LangChain and OpenAI."""

import os
import time
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

load_dotenv()

# Retry configuration
MAX_RETRIES = 3
BASE_DELAY = 0.5  # seconds


def _should_retry(exception: Exception) -> bool:
    """Check if the exception is retryable (rate limit or transient error)."""
    error_str = str(exception).lower()
    return any(phrase in error_str for phrase in ['429', 'rate limit', '503', '502', 'timeout'])


def _call_llm_with_retry(llm: ChatOpenAI, messages: List[BaseMessage], streaming: bool) -> str:
    """Call LLM with retry logic for rate limits and transient errors."""
    last_exception = None
    
    for attempt in range(MAX_RETRIES):
        try:
            if streaming:
                response_text = ""
                for chunk in llm.stream(messages):
                    response_text += chunk.content
                return response_text
            else:
                return llm.invoke(messages).content
        except Exception as e:
            last_exception = e
            if _should_retry(e) and attempt < MAX_RETRIES - 1:
                delay = BASE_DELAY * (2 ** attempt)  # Exponential backoff
                print(f"[LLM] Retry {attempt + 1}/{MAX_RETRIES} after {delay:.1f}s: {e}")
                time.sleep(delay)
            else:
                raise
    
    raise last_exception


def chatbot(
    user_message: str,
    *,
    system_prompt: str = "You are a helpful assistant.",
    conversation_history: Optional[List[Dict[str, str]]] = None,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    api_key: Optional[str] = None,
    streaming: bool = False,
    **kwargs: Any,
) -> str:
    """
    Execute a chatbot conversation using LangChain and OpenAI.

    Args:
        user_message: The user's input message.
        system_prompt: System instruction for the AI.
        conversation_history: Previous messages as list of dicts with 'role' and 'content'.
        model: OpenAI model identifier.
        temperature: Sampling temperature (0.0-2.0).
        max_tokens: Maximum tokens in response.
        api_key: OpenAI API key.
        streaming: Enable streaming responses.

    Returns:
        str: The AI's response content.
    """
    llm_params: Dict[str, Any] = {
        "model": model,
        "temperature": temperature,
        "streaming": streaming,
        **kwargs,
    }
    
    if max_tokens is not None:
        llm_params["max_tokens"] = max_tokens
    if api_key is not None:
        llm_params["api_key"] = api_key

    llm = ChatOpenAI(**llm_params)
    messages: List[BaseMessage] = [SystemMessage(content=system_prompt)]

    if conversation_history:
        for msg in conversation_history:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
            else:
                raise ValueError(f"Invalid role: {role}")

    messages.append(HumanMessage(content=user_message))

    return _call_llm_with_retry(llm, messages, streaming)

