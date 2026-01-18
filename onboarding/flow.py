"""Main onboarding flow function."""

from typing import Any, Dict, List, Optional

from onboarding.config import ONBOARDING_FIELDS, DIETARY_PREFERENCE_FLAGS
from onboarding.formatter import format_output_for_db
from onboarding.service import (
    _extract_data_with_llm,
    _should_skip_optional,
    _calculate_macros_if_ready,
    _build_completion_message,
    _extract_dietary_from_text,
)
from onboarding.flow_helpers import is_confirmation, generate_response


def onboarding(
    user_message: str,
    *,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    collected_data: Optional[Dict[str, Any]] = None,
    model: str = "gpt-4.1-mini",
    temperature: float = 0.1,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Process user response and continue onboarding flow."""
    conversation_history = list(conversation_history or [])
    collected_data = dict(collected_data or {})
    
    conversation_history.append({"role": "user", "content": user_message})
    
    # Extract data
    extracted = _extract_data_with_llm(conversation_history, model)
    
    # Update only valid onboarding fields
    for field in ONBOARDING_FIELDS:
        if field in extracted and extracted[field] is not None:
            collected_data[field] = extracted[field]
    
    # Check for macro confirmation
    macros_shown = 'metabolic_profile' in collected_data and not collected_data.get('macros_confirmed')
    if macros_shown and is_confirmation(user_message):
        collected_data['macros_confirmed'] = True
    
    if extracted.get('macros_confirmed'):
        collected_data['macros_confirmed'] = True
    
    # Extract dietary preferences AFTER macros confirmed
    if collected_data.get('macros_confirmed'):
        for pref, val in _extract_dietary_from_text(user_message).items():
            if val:
                collected_data[pref] = val
    
    # Calculate macros if ready
    macros_calculated = _calculate_macros_if_ready(collected_data)
    macros_confirmed = collected_data.get('macros_confirmed', False)
    
    # Set default target_speed if missing (optional field)
    if 'target_speed' not in collected_data:
        collected_data['target_speed'] = 'normal'
    
    # Check missing and completion - exclude target_speed as it has default
    required_fields = [f for f in ONBOARDING_FIELDS if f != 'target_speed']
    missing = [f for f in required_fields if f not in collected_data]
    
    # Check dietary - done if ANY preference captured OR user skipped
    dietary_done = any(p in collected_data for p in DIETARY_PREFERENCE_FLAGS)
    if macros_confirmed and _should_skip_optional(user_message):
        dietary_done = True
    
    is_complete = len(missing) == 0 and macros_confirmed and dietary_done
    
    if is_complete:
        msg = _build_completion_message(collected_data)
        conversation_history.append({"role": "assistant", "content": msg})
        return {
            "message": msg, "conversation_history": conversation_history,
            "collected_data": collected_data, "is_complete": True,
            "next_field": None, "metabolic_profile": collected_data.get('metabolic_profile'),
            "db_format": format_output_for_db(collected_data),
        }
    
    if not missing and macros_confirmed and not collected_data.get('dietary_asked'):
        collected_data['dietary_asked'] = True
    
    response = generate_response(
        user_message, collected_data, conversation_history,
        missing, macros_calculated, macros_confirmed, model, temperature
    )
    conversation_history.append({"role": "assistant", "content": response})
    
    return {
        "message": response, "conversation_history": conversation_history,
        "collected_data": collected_data, "is_complete": False,
        "next_field": missing[0] if missing else None,
        "metabolic_profile": collected_data.get('metabolic_profile'),
        "db_format": None,
    }
