"""Flow helper functions for onboarding."""

from typing import Any, Dict, List

from ..LLM_shared import chatbot
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
    
    if macros_confirmed:
        return "Do you have any dietary restrictions? (vegan, dairy-free, gluten-free, nut-free, pescatarian, or none)"
    print(f"Running with model: {model}"  )
    display_fields = [f for f in collected_data.keys() if f in ONBOARDING_FIELDS]
    collected_str = ", ".join(display_fields) if display_fields else "none"
    missing_str = ", ".join(missing_fields) if missing_fields else "none"
    
    system_prompt = CONVERSATION_SYSTEM_PROMPT.format(
        collected_fields=collected_str, missing_fields=missing_str,
        macros_calculated=macros_calculated, macros_confirmed=macros_confirmed,
        macro_info="",
    )
    
    try:
        msg_prompt = f"User: '{user_message}'. The NEXT missing field is '{missing_fields[0]}'. You MUST ask for it now." if missing_fields else f"User: '{user_message}'. Ask ONE question only."
        return chatbot(
            user_message=msg_prompt,
            system_prompt=system_prompt,
            conversation_history=conversation_history[:-1],
            model=model, temperature=temperature,
        )
    except Exception as e:
        print(f"Chatbot error: {e}")
        if missing_fields:
            return f"What's your {missing_fields[0].replace('_', ' ')}?"
        return "Any dietary restrictions?"
