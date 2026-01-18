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
    
    # Activity level - accept variations
    if 'activity_level' in data:
        level = str(data['activity_level']).lower().strip()
        # Map variations to valid values
        level_map = {
            'sedentary': 'sedentary', 'inactive': 'sedentary',
            'light': 'light', 'lightly active': 'light', 'lightly': 'light',
            'moderate': 'moderate', 'moderately active': 'moderate', 'moderately': 'moderate',
            'active': 'active', 'very active': 'active', 'highly active': 'active', 'very': 'active',
        }
        level = level_map.get(level, level)
        if level in ACTIVITY_MULTIPLIERS:
            validated['activity_level'] = level
    
    # Goal (normalize)
    if 'goal' in data:
        goal = str(data['goal']).lower().strip().replace(' ', '_')
        goal_map = {
            'lose': 'lose_weight', 'cut': 'lose_weight', 'lose_weight': 'lose_weight',
            'gain': 'gain_weight', 'bulk': 'gain_weight', 'gain_weight': 'gain_weight',
            'gain_muscle': 'gain_weight', 'build_muscle': 'gain_weight',
            'maintain': 'maintain', 'maintenance': 'maintain',
        }
        goal = goal_map.get(goal, goal)
        if goal in ('lose_weight', 'maintain', 'gain_weight'):
            validated['goal'] = goal
    
    # Target speed
    if 'target_speed' in data:
        speed = str(data['target_speed']).lower().strip()
        if speed in TARGET_SPEED_RATES:
            validated['target_speed'] = speed
    
    # Numeric fields with embedded unit extraction
    _validate_numeric_with_units(data, validated)
    
    # Macros confirmed
    if 'macros_confirmed' in data:
        val = data['macros_confirmed']
        if val is True or (isinstance(val, str) and val.lower() in ('true', 'yes', 'confirm', 'ok')):
            validated['macros_confirmed'] = True
    
    return validated


def _validate_numeric_with_units(data: Dict[str, Any], validated: Dict[str, Any]) -> None:
    """Validate numeric fields and extract embedded units."""
    # Height
    if 'current_height' in data:
        val = data['current_height']
        num, unit = _extract_number_and_unit(val, 'height')
        if num and num > 0:
            validated['current_height'] = num
            if unit:
                validated['current_height_unit'] = unit
    
    if 'current_height_unit' in data and 'current_height_unit' not in validated:
        unit = str(data['current_height_unit']).lower().strip()
        if unit in ('in', 'inch', 'inches', 'feet', 'foot', 'ft'):
            validated['current_height_unit'] = 'in'
        elif unit in ('cm', 'centimeter', 'centimeters'):
            validated['current_height_unit'] = 'cm'
    
    # Weight fields
    for field, unit_field in [
        ('current_weight', 'current_weight_unit'),
        ('target_weight', 'target_weight_unit')
    ]:
        if field in data:
            val = data[field]
            num, unit = _extract_number_and_unit(val, 'weight')
            if num and num > 0:
                validated[field] = num
                if unit:
                    validated[unit_field] = unit
        
        if unit_field in data and unit_field not in validated:
            unit = str(data[unit_field]).lower().strip()
            if unit in ('lb', 'lbs', 'pound', 'pounds'):
                validated[unit_field] = 'lb'
            elif unit in ('kg', 'kilo', 'kilos', 'kilogram', 'kilograms'):
                validated[unit_field] = 'kg'


def _extract_number_and_unit(val: Any, field_type: str) -> tuple:
    """Extract number and unit from a value like '80kg' or '5.9 feet'."""
    if isinstance(val, (int, float)):
        return float(val), None
    
    text = str(val).lower().strip()
    
    # Try to extract number
    num_match = re.search(r'[\d.]+', text)
    if not num_match:
        return None, None
    
    num = float(num_match.group())
    
    # Try to extract unit
    unit = None
    if field_type == 'weight':
        if 'kg' in text or 'kilo' in text:
            unit = 'kg'
        elif 'lb' in text or 'pound' in text:
            unit = 'lb'
    elif field_type == 'height':
        if 'cm' in text or 'cent' in text:
            unit = 'cm'
        elif 'in' in text or 'feet' in text or 'foot' in text or 'ft' in text or "'" in text:
            unit = 'in'
    
    return num, unit
