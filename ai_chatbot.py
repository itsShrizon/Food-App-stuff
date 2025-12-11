"""Simple AI chatbot using the shared LLM wrapper."""

from typing import Any, Dict, List, Optional

from LLM_shared import chatbot


def _format_user_info(user_info: Dict[str, Any]) -> str:
    """Format user profile into a short, readable block."""
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
    """Chat using the shared LLM wrapper with simple history handling."""

    history: List[Dict[str, str]] = conversation_history[:] if conversation_history else []

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


if __name__ == "__main__":
    demo_user = {
        "gender": "male",
        "date_of_birth": "1990-01-01",
        "current_height": 180,
        "current_height_unit": "cm",
        "current_weight": 80,
        "current_weight_unit": "kg",
        "target_weight": 75,
        "target_weight_unit": "kg",
        "goal": "lose_weight",
        "activity_level": "moderate",
    }

    chat_history: List[Dict[str, str]] = []
    chat_history.append({"role": "assistant", "content": "Hi! How can I help with your plan today?"})

    reply = ai_chatbot(
        "Suggest a quick healthy dinner from pantry items.",
        demo_user,
        conversation_history=chat_history,
    )
    print(reply["response"])
