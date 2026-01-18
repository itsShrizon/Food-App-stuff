"""Main onboarding service - orchestrates the onboarding flow."""

from typing import Any, Dict, List, Optional

from LLM_shared import chatbot
from onboarding.config import ONBOARDING_FIELDS, DIETARY_PREFERENCE_FLAGS
from onboarding.prompts import EXTRACTION_SYSTEM_PROMPT, CONVERSATION_SYSTEM_PROMPT
from onboarding.utils import safe_parse_json, calculate_age
from onboarding.validators import validate_extracted_data
from onboarding.calculator import calculate_metabolic_profile
from onboarding.formatter import format_output_for_db


def _extract_data_with_llm(
    conversation_history: List[Dict[str, str]],
    model: str = "gpt-4.1-nano",
) -> Dict[str, Any]:
    """Extract data from conversation using LLM."""
    conversation_text = "\n".join([
        f"{msg['role']}: {msg['content']}" for msg in conversation_history
    ])
    
    try:
        response = chatbot(
            user_message=f"Extract data from:\n{conversation_text}\n\nReturn ONLY JSON.",
            system_prompt=EXTRACTION_SYSTEM_PROMPT,
            model=model,
            temperature=0.0,
        )
        return validate_extracted_data(safe_parse_json(response))
    except Exception as e:
        print(f"Extraction error (failsafe): {e}")
        return {}


def _should_skip_optional(user_message: str) -> bool:
    """Check if user wants to skip optional fields."""
    skip_words = ['skip', 'none', 'no ', 'nothing', "don't have", "no restrictions"]
    return any(kw in user_message.lower() for kw in skip_words)


def _has_all_for_macros(data: Dict[str, Any]) -> bool:
    """Check if we have all fields needed for macro calculation."""
    required = [
        'gender', 'date_of_birth', 'current_height', 'current_height_unit',
        'current_weight', 'current_weight_unit', 'target_weight', 
        'target_weight_unit', 'activity_level', 'goal'
    ]
    return all(f in data for f in required)


def _calculate_macros_if_ready(collected_data: Dict[str, Any]) -> bool:
    """Calculate metabolic profile if ready. Returns True if calculated."""
    if 'metabolic_profile' in collected_data or not _has_all_for_macros(collected_data):
        return 'metabolic_profile' in collected_data
    
    try:
        collected_data['metabolic_profile'] = calculate_metabolic_profile(
            gender=collected_data['gender'],
            weight=collected_data['current_weight'],
            weight_unit=collected_data['current_weight_unit'],
            height=collected_data['current_height'],
            height_unit=collected_data['current_height_unit'],
            age=calculate_age(collected_data['date_of_birth']),
            activity_level=collected_data['activity_level'],
            goal=collected_data['goal'],
            target_weight=collected_data['target_weight'],
            target_weight_unit=collected_data['target_weight_unit'],
            target_speed=collected_data.get('target_speed', 'normal'),
        )
        return True
    except Exception as e:
        print(f"Macro calculation error (failsafe): {e}")
        return False


def _build_completion_message(collected_data: Dict[str, Any]) -> str:
    """Build the completion message with macro summary."""
    msg = "Thank you! Your profile is complete!\n\n"
    if 'metabolic_profile' in collected_data:
        mp = collected_data['metabolic_profile']
        msg += f"**Your Daily Targets:**\n"
        msg += f"- Calories: {mp['daily_calorie_target']} kcal\n"
        msg += f"- Protein: {mp['protein_g']}g | Carbs: {mp['carbs_g']}g | Fat: {mp['fats_g']}g\n"
        if mp['estimated_weeks_to_goal'] > 0:
            msg += f"\nEstimated time to goal: {mp['estimated_weeks_to_goal']} weeks"
    return msg
