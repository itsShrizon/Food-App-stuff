"""AI Chatbot service for personalized fitness assistance."""

from typing import Any, Dict, List, Optional

from ..core.llm import chatbot


def _format_user_info(user_info: Dict[str, Any]) -> str:
    """Format user profile into a readable block."""
    lines = [f"- {k.replace('_', ' ').title()}: {v}" for k, v in sorted(user_info.items())]
    return "\n".join(lines)


def ai_chatbot(
    user_message: str,
    user_info: Dict[str, Any],
    conversation_history: Optional[List[Dict[str, str]]] = None,
    *,
    system_prompt: str = "You are a helpful assistant.",
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    streaming: bool = True,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Chat using the shared LLM wrapper with user context.
    
    Args:
        user_message: The user's message.
        user_info: User profile information.
        conversation_history: Previous messages.
        system_prompt: System prompt for the AI.
        model: LLM model to use.
        temperature: Model temperature.
        streaming: Enable streaming.
        
    Returns:
        Dictionary with 'response' and 'history'.
    """
    history = list(conversation_history) if conversation_history else []

    profile_block = _format_user_info(user_info)
    prompt = f"{system_prompt}\n\nUser Profile:\n{profile_block}"

    result = chatbot(
        user_message=user_message,
        system_prompt=prompt,
        conversation_history=history,
        model=model,
        temperature=temperature,
        streaming=streaming,
        **kwargs,
    )

    updated_history = history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": result},
    ]

    return {"response": result, "history": updated_history}
