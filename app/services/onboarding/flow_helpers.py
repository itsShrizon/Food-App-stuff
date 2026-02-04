"""Flow helper functions for onboarding."""

from typing import Any, Dict, List

import app.core.llm as llm_module
from .config import ONBOARDING_FIELDS
from .prompts import CONVERSATION_SYSTEM_PROMPT


CONFIRM_WORDS = [
    'yes', 'yeah', 'yep', 'yup', 'sure', 'ok', 'okay', 'confirm', 
    'looks good', 'look good', 'sounds good', 'perfect', 'great',
    'thank', 'thanks', 'correct', 'right', 'good', "that's fine",
    'fine', 'proceed', 'continue', 'go ahead'
]


def is_confirmation(text: str) -> bool:
    """Check if user text is a confirmation."""
    text = text.lower().strip()
    return any(word in text for word in CONFIRM_WORDS)


def generate_macro_display(collected_data: Dict[str, Any]) -> str:
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


def generate_response(
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
    if macros_calculated and not macros_confirmed and 'metabolic_profile' in collected_data:
        return generate_macro_display(collected_data)
    
    display_fields = [f for f in collected_data.keys() if f in ONBOARDING_FIELDS]
    
    # Add dietary flags to display
    from .config import DIETARY_PREFERENCE_FLAGS
    active_dietary = [f for f in DIETARY_PREFERENCE_FLAGS if collected_data.get(f)]
    if active_dietary:
        display_fields.append(f"dietary: {', '.join(active_dietary)}")
    elif collected_data.get('dietary_none_stated'):
         display_fields.append("dietary: none")
         
    collected_str = ", ".join(display_fields) if display_fields else "none"
    missing_str = ", ".join(missing_fields) if missing_fields else "none"
    
    system_prompt = CONVERSATION_SYSTEM_PROMPT.format(
        collected_fields=collected_str, missing_fields=missing_str,
        macros_calculated=macros_calculated, macros_confirmed=macros_confirmed,
        macro_info="",
    )
    
    try:
        msg_prompt = f"User: '{user_message}'. The NEXT missing field is '{missing_fields[0]}'. You MUST ask for it now." if missing_fields else f"User: '{user_message}'. Ask ONE question only."
        return llm_module.chatbot(
        user_message=user_message,
        system_prompt=system_prompt,
        conversation_history=conversation_history,
        model=model,
        temperature=temperature,
    )
    except Exception as e:
        print(f"Chatbot error: {e}")
        if missing_fields:
            return f"What's your {missing_fields[0].replace('_', ' ')}?"
        return "Any dietary restrictions?"
