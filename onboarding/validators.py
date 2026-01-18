"""Validation functions for extracted onboarding data."""

import re
from datetime import datetime
from typing import Any, Dict

from onboarding.config import (
    ACTIVITY_MULTIPLIERS,
    DIETARY_PREFERENCE_FLAGS,
    TARGET_SPEED_RATES,
)


def validate_extracted_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize LLM-extracted data."""
    validated = {}
    
    # Gender
    if 'gender' in data:
        gender = str(data['gender']).lower().strip()
        gender_map = {'m': 'male', 'f': 'female', 'other': 'others'}
        gender = gender_map.get(gender, gender)
        if gender in ('male', 'female', 'others'):
            validated['gender'] = gender
    
    # Date of birth
    if 'date_of_birth' in data:
        dob = str(data['date_of_birth']).strip()
        try:
            datetime.strptime(dob, "%Y-%m-%d")
            validated['date_of_birth'] = dob
        except ValueError:
            pass
    
    # Activity level
    if 'activity_level' in data:
        level = str(data['activity_level']).lower().strip()
        if level in ACTIVITY_MULTIPLIERS:
            validated['activity_level'] = level
    
    # Goal (normalize)
    if 'goal' in data:
        goal = str(data['goal']).lower().strip().replace(' ', '_')
        goal_map = {'lose': 'lose_weight', 'cut': 'lose_weight', 
                    'gain': 'gain_weight', 'bulk': 'gain_weight'}
        goal = goal_map.get(goal, goal)
        if goal in ('lose_weight', 'maintain', 'gain_weight'):
            validated['goal'] = goal
    
    # Target speed
    if 'target_speed' in data:
        speed = str(data['target_speed']).lower().strip()
        if speed in TARGET_SPEED_RATES:
            validated['target_speed'] = speed
    
    # Numeric fields
    for field in ['current_height', 'current_weight', 'target_weight']:
        if field in data:
            try:
                val = data[field]
                if isinstance(val, (int, float)):
                    validated[field] = float(val)
                else:
                    num = re.search(r'[\d.]+', str(val))
                    if num:
                        validated[field] = float(num.group())
            except (ValueError, TypeError):
                pass
    
    # Unit fields
    _validate_units(data, validated)
    
    # Dietary preferences
    for pref in DIETARY_PREFERENCE_FLAGS:
        if pref in data:
            val = data[pref]
            validated[pref] = val if isinstance(val, bool) else str(val).lower() in ('true', 'yes', '1')
    
    # Macros confirmed
    if 'macros_confirmed' in data:
        val = data['macros_confirmed']
        validated['macros_confirmed'] = val if isinstance(val, bool) else str(val).lower() in ('true', 'yes', 'ok')
    
    return validated


def _validate_units(data: Dict[str, Any], validated: Dict[str, Any]) -> None:
    """Validate height and weight unit fields."""
    if 'current_height_unit' in data:
        unit = str(data['current_height_unit']).lower().strip()
        validated['current_height_unit'] = 'in' if unit in ('in', 'inch', 'inches') else 'cm'
    
    for field in ['current_weight_unit', 'target_weight_unit']:
        if field in data:
            unit = str(data[field]).lower().strip()
            validated[field] = 'lb' if unit in ('lb', 'lbs', 'pound', 'pounds') else 'kg'
