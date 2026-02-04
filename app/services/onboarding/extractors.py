"""Numeric field extraction and validation."""

import re
from typing import Any, Dict, Tuple, Optional


def _validate_numeric_with_units(data: Dict[str, Any], validated: Dict[str, Any]) -> None:
    """Validate numeric fields and extract embedded units."""
    # Height
    if 'current_height' in data:
        num, unit = _extract_number_and_unit(data['current_height'], 'height')
        # Only save if unit is found OR if we already have a unit in validated/data
        existing_unit = validated.get('current_height_unit') or data.get('current_height_unit')
        
        if num and num > 0:
            if unit:
                validated['current_height'] = num
                validated['current_height_unit'] = unit
            elif existing_unit:
                validated['current_height'] = num
            # If no unit found and no existing unit, DO NOT save height. Bot will ask again.
    
    if 'current_height_unit' in data and 'current_height_unit' not in validated:
        unit = _normalize_height_unit(str(data['current_height_unit']))
        if unit:
            validated['current_height_unit'] = unit
    
    # Weight fields
    for field, unit_field in [('current_weight', 'current_weight_unit'), ('target_weight', 'target_weight_unit')]:
        if field in data:
            num, unit = _extract_number_and_unit(data[field], 'weight')
            existing_unit = validated.get(unit_field) or data.get(unit_field)
            
            if num and num > 0:
                if unit:
                    validated[field] = num
                    validated[unit_field] = unit
                elif existing_unit:
                    validated[field] = num
                # If no unit found/existing, ignore value
        
        if unit_field in data and unit_field not in validated:
            unit = _normalize_weight_unit(str(data[unit_field]))
            if unit:
                validated[unit_field] = unit


def _extract_number_and_unit(val: Any, field_type: str) -> Tuple[Optional[float], Optional[str]]:
    """Extract number and unit from a value like '80kg' or '5.9 feet'."""
    if isinstance(val, (int, float)):
        return float(val), None
    
    text = str(val).lower().strip()
    num_match = re.search(r'[\d.]+', text)
    if not num_match:
        return None, None
    
    num = float(num_match.group())
    unit = None
    
    if field_type == 'weight':
        if 'kg' in text or 'kilo' in text:
            unit = 'kg'
        elif 'lb' in text or 'pound' in text:
            unit = 'lb'
    elif field_type == 'height':
        if 'cm' in text or 'cent' in text:
            unit = 'cm'
        elif any(x in text for x in ('in', 'feet', 'foot', 'ft', "'")):
            unit = 'in'
    
    return num, unit


def _normalize_height_unit(unit: str) -> Optional[str]:
    """Normalize height unit string."""
    unit = unit.lower().strip()
    if unit in ('in', 'inch', 'inches', 'feet', 'foot', 'ft'):
        return 'in'
    elif unit in ('cm', 'centimeter', 'centimeters'):
        return 'cm'
    return None


def _normalize_weight_unit(unit: str) -> Optional[str]:
    """Normalize weight unit string."""
    unit = unit.lower().strip()
    if unit in ('lb', 'lbs', 'pound', 'pounds'):
        return 'lb'
    elif unit in ('kg', 'kilo', 'kilos', 'kilogram', 'kilograms'):
        return 'kg'
    return None
