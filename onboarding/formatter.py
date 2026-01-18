"""DB format output formatting for onboarding."""

from typing import Any, Dict

from onboarding.config import DIETARY_PREFERENCE_FLAGS


def get_default_dietary_preferences() -> Dict[str, bool]:
    """Return default dietary preferences (all False)."""
    return {pref: False for pref in DIETARY_PREFERENCE_FLAGS}


def build_dietary_preferences(collected_data: Dict[str, Any]) -> Dict[str, bool]:
    """Build dietary preferences object from collected data."""
    prefs = get_default_dietary_preferences()
    for pref in DIETARY_PREFERENCE_FLAGS:
        if pref in collected_data:
            prefs[pref] = bool(collected_data[pref])
    return prefs


def format_output_for_db(collected_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format collected data to match the DB structure."""
    onboarding = {
        'gender': collected_data.get('gender', ''),
        'date_of_birth': collected_data.get('date_of_birth', ''),
        'current_height': collected_data.get('current_height', 0),
        'current_height_unit': collected_data.get('current_height_unit', 'cm'),
        'current_weight': collected_data.get('current_weight', 0),
        'current_weight_unit': collected_data.get('current_weight_unit', 'kg'),
        'target_weight': collected_data.get('target_weight', 0),
        'target_weight_unit': collected_data.get('target_weight_unit', 'kg'),
        'goal': collected_data.get('goal', 'maintain'),
        'target_speed': collected_data.get('target_speed', 'normal'),
        'activity_level': collected_data.get('activity_level', 'moderate'),
        'dietary_preferences': build_dietary_preferences(collected_data),
    }
    
    metabolic_profile = collected_data.get('metabolic_profile', {
        'daily_calorie_target': 0.0,
        'protein_g': 0.0,
        'carbs_g': 0.0,
        'fats_g': 0.0,
        'tdee': 0.0,
        'bmr': 0.0,
        'estimated_weeks_to_goal': 0.0,
    })
    
    return {
        'onboarding': onboarding,
        'metabolic_profile': metabolic_profile,
    }
