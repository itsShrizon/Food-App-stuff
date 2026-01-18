"""Main onboarding flow functions."""

from typing import Any, Dict, List, Optional

from LLM_shared import chatbot
from onboarding.config import ONBOARDING_FIELDS, DIETARY_PREFERENCE_FLAGS
from onboarding.prompts import CONVERSATION_SYSTEM_PROMPT
from onboarding.formatter import format_output_for_db
from onboarding.service import (
    _extract_data_with_llm,
    _should_skip_optional,
    _calculate_macros_if_ready,
    _build_completion_message,
)


def _generate_response(
    user_message: str,
    collected_data: Dict[str, Any],
    conversation_history: List[Dict[str, str]],
    missing_fields: List[str],
    macros_calculated: bool,
    macros_confirmed: bool,
    model: str,
    temperature: float,
) -> str:
    """Generate AI response for the conversation."""
    collected_str = ", ".join(collected_data.keys()) if collected_data else "none"
    missing_str = ", ".join(missing_fields) if missing_fields else "none"
    
    # Build macro info
    macro_info = ""
    if macros_calculated and not macros_confirmed:
        mp = collected_data['metabolic_profile']
        macro_info = f"""
Show macros and ask for confirmation:
- Calories: {mp['daily_calorie_target']} kcal | Protein: {mp['protein_g']}g
- Carbs: {mp['carbs_g']}g | Fat: {mp['fats_g']}g
- Weeks to goal: {mp['estimated_weeks_to_goal']}"""
    elif macros_confirmed:
        macro_info = "Macros confirmed! Ask about dietary preferences (vegan, dairy-free, etc.)"
    
    system_prompt = CONVERSATION_SYSTEM_PROMPT.format(
        collected_fields=collected_str, missing_fields=missing_str,
        macros_calculated=macros_calculated, macros_confirmed=macros_confirmed,
        macro_info=macro_info,
    )
    
    try:
        return chatbot(
            user_message=f"User said: '{user_message}'. Continue naturally.",
            system_prompt=system_prompt,
            conversation_history=conversation_history[:-1],
            model=model, temperature=temperature,
        )
    except Exception as e:
        print(f"Chatbot error (failsafe): {e}")
        if missing_fields:
            return f"Could you tell me about your {missing_fields[0].replace('_', ' ')}?"
        return "Do you have any dietary preferences I should know about?"


def onboarding(
    user_message: str,
    *,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    collected_data: Optional[Dict[str, Any]] = None,
    model: str = "gpt-4.1-nano",
    temperature: float = 0.1,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Process user response and continue onboarding flow."""
    conversation_history = list(conversation_history or [])
    collected_data = dict(collected_data or {})
    
    conversation_history.append({"role": "user", "content": user_message})
    
    # Extract and update data
    extracted = _extract_data_with_llm(conversation_history, model)
    all_fields = ONBOARDING_FIELDS + DIETARY_PREFERENCE_FLAGS + ('macros_confirmed',)
    for field, value in extracted.items():
        if field in all_fields and value is not None:
            collected_data[field] = value
    
    # Calculate macros if ready
    macros_calculated = _calculate_macros_if_ready(collected_data)
    macros_confirmed = collected_data.get('macros_confirmed', False)
    
    # Default target_speed
    if 'target_speed' not in collected_data:
        collected_data['target_speed'] = 'normal'
    
    # Check completion
    missing = [f for f in ONBOARDING_FIELDS if f not in collected_data]
    dietary_done = any(p in collected_data for p in DIETARY_PREFERENCE_FLAGS)
    
    is_complete = (
        len(missing) == 0 and macros_confirmed and
        (dietary_done or collected_data.get('dietary_skipped') or _should_skip_optional(user_message))
    )
    
    if _should_skip_optional(user_message) and not missing and macros_confirmed:
        collected_data['dietary_skipped'] = True
        is_complete = True
    
    if is_complete:
        msg = _build_completion_message(collected_data)
        conversation_history.append({"role": "assistant", "content": msg})
        return {
            "message": msg, "conversation_history": conversation_history,
            "collected_data": collected_data, "is_complete": True,
            "next_field": None, "metabolic_profile": collected_data.get('metabolic_profile'),
            "db_format": format_output_for_db(collected_data),
        }
    
    # Generate response
    response = _generate_response(
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
