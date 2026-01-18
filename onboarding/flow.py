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
    _extract_dietary_from_text,
)


def _is_confirmation(text: str) -> bool:
    """Check if user text is a confirmation."""
    text = text.lower().strip()
    confirm_words = [
        'yes', 'yeah', 'yep', 'yup', 'sure', 'ok', 'okay', 'confirm', 
        'looks good', 'look good', 'sounds good', 'perfect', 'great',
        'thank', 'thanks', 'correct', 'right', 'good', "that's fine",
        'fine', 'proceed', 'continue', 'go ahead'
    ]
    return any(word in text for word in confirm_words)


def _generate_macro_display(collected_data: Dict[str, Any]) -> str:
    """Generate the macro display message."""
    mp = collected_data['metabolic_profile']
    msg = f"""Here are your recommended daily targets:

📊 **Calories:** {mp['daily_calorie_target']} kcal
🥩 **Protein:** {mp['protein_g']}g
🍞 **Carbs:** {mp['carbs_g']}g
🧈 **Fat:** {mp['fats_g']}g"""
    
    if mp.get('estimated_days_to_goal', 0) > 0:
        msg += f"\n⏱️ **Estimated time to goal:** {mp['estimated_days_to_goal']} days"
    
    msg += "\n\nDoes this look good to you?"
    return msg


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
    # If macros just calculated and NOT confirmed yet, show them
    if macros_calculated and not macros_confirmed and 'metabolic_profile' in collected_data:
        return _generate_macro_display(collected_data)
    
    # If macros confirmed, ask about dietary
    if macros_confirmed:
        return "Do you have any dietary restrictions? (vegan, dairy-free, gluten-free, nut-free, pescatarian, or none)"
    
    display_fields = [f for f in collected_data.keys() if f in ONBOARDING_FIELDS]
    collected_str = ", ".join(display_fields) if display_fields else "none"
    missing_str = ", ".join(missing_fields) if missing_fields else "none"
    
    system_prompt = CONVERSATION_SYSTEM_PROMPT.format(
        collected_fields=collected_str, missing_fields=missing_str,
        macros_calculated=macros_calculated, macros_confirmed=macros_confirmed,
        macro_info="",
    )
    
    try:
        return chatbot(
            user_message=f"User: '{user_message}'. Ask ONE question only.",
            system_prompt=system_prompt,
            conversation_history=conversation_history[:-1],
            model=model, temperature=temperature,
        )
    except Exception as e:
        print(f"Chatbot error: {e}")
        if missing_fields:
            return f"What's your {missing_fields[0].replace('_', ' ')}?"
        return "Any dietary restrictions?"


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
    
    # Extract data
    extracted = _extract_data_with_llm(conversation_history, model)
    
    # Update only valid onboarding fields
    for field in ONBOARDING_FIELDS:
        if field in extracted and extracted[field] is not None:
            collected_data[field] = extracted[field]
    
    # Check for macro confirmation - DIRECTLY from user message
    macros_were_shown = 'metabolic_profile' in collected_data and not collected_data.get('macros_confirmed')
    if macros_were_shown and _is_confirmation(user_message):
        collected_data['macros_confirmed'] = True
    
    # Also check from extraction
    if extracted.get('macros_confirmed'):
        collected_data['macros_confirmed'] = True
    
    # Extract dietary preferences AFTER macros confirmed
    if collected_data.get('macros_confirmed'):
        dietary = _extract_dietary_from_text(user_message)
        for pref, val in dietary.items():
            if val:
                collected_data[pref] = val
    
    # Calculate macros if ready
    macros_calculated = _calculate_macros_if_ready(collected_data)
    macros_confirmed = collected_data.get('macros_confirmed', False)
    
    # Check missing required fields
    missing = [f for f in ONBOARDING_FIELDS if f not in collected_data]
    
    # Check dietary completion
    dietary_asked = collected_data.get('dietary_asked', False)
    dietary_done = any(p in collected_data for p in DIETARY_PREFERENCE_FLAGS)
    
    # Handle skip/none for dietary
    if macros_confirmed and _should_skip_optional(user_message):
        dietary_done = True
    
    is_complete = len(missing) == 0 and macros_confirmed and dietary_done
    
    if is_complete:
        msg = _build_completion_message(collected_data)
        conversation_history.append({"role": "assistant", "content": msg})
        return {
            "message": msg, 
            "conversation_history": conversation_history,
            "collected_data": collected_data, 
            "is_complete": True,
            "next_field": None, 
            "metabolic_profile": collected_data.get('metabolic_profile'),
            "db_format": format_output_for_db(collected_data),
        }
    
    # Mark dietary as asked after macros confirmed
    if not missing and macros_confirmed and not dietary_asked:
        collected_data['dietary_asked'] = True
    
    response = _generate_response(
        user_message, collected_data, conversation_history,
        missing, macros_calculated, macros_confirmed, model, temperature
    )
    conversation_history.append({"role": "assistant", "content": response})
    
    return {
        "message": response, 
        "conversation_history": conversation_history,
        "collected_data": collected_data, 
        "is_complete": False,
        "next_field": missing[0] if missing else None,
        "metabolic_profile": collected_data.get('metabolic_profile'),
        "db_format": None,
    }
