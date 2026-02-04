"""Start onboarding function."""

from typing import Any, Dict

import app.core.llm as llm_module
from .config import ONBOARDING_FIELDS
from .prompts import CONVERSATION_SYSTEM_PROMPT


def start_onboarding(
    *,
    model: str = "gpt-4.1-2025-04-14",
    temperature: float = 0.3,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Start a new onboarding conversation."""
    missing_str = ", ".join(ONBOARDING_FIELDS)
    
    system_prompt = CONVERSATION_SYSTEM_PROMPT.format(
        collected_fields="none",
        missing_fields=missing_str,
        macros_calculated=False,
        macros_confirmed=False,
        macro_info="",
    )

    try:
        welcome = llm_module.chatbot(
            user_message="Hi",
            system_prompt=CONVERSATION_SYSTEM_PROMPT,
            model=model,
            temperature=temperature,
            **kwargs,
        )
    except Exception as e:
        print(f"Start error (failsafe): {e}")
        welcome = "Hey! I'm excited to help you on your fitness journey! What's your gender"

    return {
        'message': welcome,
        'is_complete': False,
        'collected_data': {},
        'conversation_history': [{"role": "assistant", "content": welcome}],
        'next_field': 'gender',
        'metabolic_profile': None,
        'db_format': None,
    }
