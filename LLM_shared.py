"""Chatbot module using LangChain and OpenAI."""

import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

load_dotenv()


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
        system_prompt: System instruction for the AI. Defaults to "You are a helpful assistant."
        conversation_history: Previous messages as list of dicts with 'role' and 'content'.
            Example: [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello!"}]
        model: OpenAI model identifier. Defaults to "gpt-3.5-turbo".
        temperature: Sampling temperature (0.0-2.0). Defaults to 0.7.
        max_tokens: Maximum tokens in response. Defaults to None.
        api_key: OpenAI API key. Defaults to None (uses OPENAI_API_KEY from .env file).
        streaming: Enable streaming responses. Defaults to False.
        **kwargs: Additional arguments passed to ChatOpenAI.

    Returns:
        str: The AI's response content.

    Raises:
        ValueError: If conversation_history contains invalid role types.
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
                raise ValueError(f"Invalid role: {role}. Must be 'user' or 'assistant'.")

    messages.append(HumanMessage(content=user_message))

    if streaming:
        response_text = ""
        for chunk in llm.stream(messages):
            response_text += chunk.content
        return response_text
    
    response = llm.invoke(messages)
    return response.content
