"""Validation helper functions for onboarding data extraction."""

import re
from typing import Any, Dict, Tuple

from .config import ACTIVITY_MULTIPLIERS, TARGET_SPEED_RATES, DIETARY_PREFERENCE_FLAGS
from .extractors import _validate_numeric_with_units


def validate_extracted_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize LLM-extracted data."""
    validated = {}
    
    _validate_gender(data, validated)
    _validate_date_of_birth(data, validated)
    _validate_activity_level(data, validated)
    _validate_goal(data, validated)
    _validate_target_speed(data, validated)
    _validate_numeric_with_units(data, validated)
    _validate_macros_confirmed(data, validated)
    _validate_dietary(data, validated)
    _validate_age(data, validated)
    
    return validated


def _validate_gender(data: Dict[str, Any], validated: Dict[str, Any]) -> None:
    if 'gender' not in data:
        return
    gender = str(data['gender']).lower().strip()
    gender_map = {'m': 'male', 'f': 'female', 'other': 'others'}
    gender = gender_map.get(gender, gender)
    if gender in ('male', 'female', 'others'):
        validated['gender'] = gender


def _validate_date_of_birth(data: Dict[str, Any], validated: Dict[str, Any]) -> None:
    if 'date_of_birth' not in data:
        return
    from datetime import datetime
    dob = str(data['date_of_birth']).strip()
    try:
        datetime.strptime(dob, "%Y-%m-%d")
        validated['date_of_birth'] = dob
    except ValueError:
        pass


def _validate_activity_level(data: Dict[str, Any], validated: Dict[str, Any]) -> None:
    if 'activity_level' not in data:
        return
    level = str(data['activity_level']).lower().strip()
    
    # Extended mapping for conversational inputs
    level_map = {
        'sedentary': 'sedentary', 'inactive': 'sedentary', 'desk': 'sedentary',
        'office': 'sedentary', 'desk_job': 'sedentary', 'sitting': 'sedentary',
        'light': 'light', 'lightly_active': 'light', 'lightly': 'light',
        'some_exercise': 'light', 'walk': 'light', 'walking': 'light',
        'moderate': 'moderate', 'moderately_active': 'moderate', 'regular': 'moderate',
        'gym': 'moderate', 'workout': 'moderate', 'exercise': 'moderate',
        'active': 'active', 'very_active': 'active', 'highly_active': 'active',
        'athlete': 'active', 'sports': 'active', 'daily_exercise': 'active',
        'run': 'active', 'running': 'active',
    }
    
    # Normalize: replace spaces/hyphens with underscores
    normalized = level.replace(' ', '_').replace('-', '_')
    level = level_map.get(normalized, level_map.get(level, level))
    
    if level in ACTIVITY_MULTIPLIERS:
        validated['activity_level'] = level


def _validate_goal(data: Dict[str, Any], validated: Dict[str, Any]) -> None:
    if 'goal' not in data:
        return
    goal = str(data['goal']).lower().strip().replace(' ', '_')
    goal_map = {
        'lose': 'lose_weight', 'cut': 'lose_weight', 'lose_weight': 'lose_weight',
        'gain': 'gain_weight', 'bulk': 'gain_weight', 'gain_weight': 'gain_weight',
        'maintain': 'maintain', 'maintenance': 'maintain',
    }
    goal = goal_map.get(goal, goal)
    if goal in ('lose_weight', 'maintain', 'gain_weight'):
        validated['goal'] = goal


def _validate_target_speed(data: Dict[str, Any], validated: Dict[str, Any]) -> None:
    if 'target_speed' not in data:
        return
    speed = str(data['target_speed']).lower().strip()
    if speed in TARGET_SPEED_RATES:
        validated['target_speed'] = speed


def _validate_macros_confirmed(data: Dict[str, Any], validated: Dict[str, Any]) -> None:
    if 'macros_confirmed' not in data:
        return
    val = data['macros_confirmed']
    if val is True or (isinstance(val, str) and val.lower() in ('true', 'yes', 'confirm')):
        validated['macros_confirmed'] = True


def _validate_dietary(data: Dict[str, Any], validated: Dict[str, Any]) -> None:
    if 'dietary' not in data:
        return
    
    dietary = data['dietary']
    
    # Handle single string value (convert to list)
    if isinstance(dietary, str):
        dietary = [dietary]
    
    if not isinstance(dietary, list):
        return
    
    validated_dietary = []
    for item in dietary:
        item_str = str(item).lower().strip().replace(' ', '_').replace('-', '_')
        
        # Expanded mapping for negative/none responses
        none_phrases = [
            'none', 'no', 'nope', 'nothing', 'nada', 'n/a', 'na', 'no_restrictions',
            'nothing_really', 'not_really', 'nah', 'no_preferences', 'no_dietary',
            'no_allergies', 'none_at_all', 'nothing_special', 'i_eat_everything',
            'eat_everything', 'no_issues', 'no_food_allergies', 'all_good',
        ]
        if item_str in none_phrases or item_str.startswith('nothing') or item_str.startswith('no_'):
            validated_dietary.append('none')
            continue
            
        # Map common variations
        item_map = {
            'dairy': 'dairy_free', 'no_dairy': 'dairy_free', 'lactose': 'dairy_free',
            'lactose_intolerant': 'dairy_free', 'lactose_free': 'dairy_free',
            'no_gluten': 'gluten_free', 'gluten': 'gluten_free', 'celiac': 'gluten_free',
            'coeliac': 'gluten_free',
            'no_nut': 'nut_free', 'nut': 'nut_free', 'no_nuts': 'nut_free',
            'nut_allergy': 'nut_free', 'peanut': 'nut_free', 'peanut_allergy': 'nut_free',
            'pesc': 'pescatarian', 'fish_only': 'pescatarian',
            'vegetarian': 'vegan',  # Close enough for flags
            'plant_based': 'vegan',
        }
        item_str = item_map.get(item_str, item_str)
        
        if item_str in DIETARY_PREFERENCE_FLAGS:
            validated_dietary.append(item_str)
            
    if validated_dietary:
        validated['dietary'] = list(set(validated_dietary))


def _validate_age(data: Dict[str, Any], validated: Dict[str, Any]) -> None:
    if 'age' not in data:
        return
    try:
        age_val = int(str(data['age']).strip())
        if 0 < age_val < 120:
            validated['age'] = age_val
    except ValueError:
        pass

