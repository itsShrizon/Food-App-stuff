"""
Onboarding Module Facade

This file provides backward-compatible imports from the layered onboarding package.
The actual implementation is in the onboarding/ package directory.

Architecture:
    onboarding/
    ├── __init__.py     - Package exports
    ├── config.py       - Constants and field definitions
    ├── prompts.py      - LLM prompt templates
    ├── utils.py        - JSON parsing, age calculation, unit conversions
    ├── validators.py   - Data validation and sanitization
    ├── calculator.py   - Metabolic profile calculations
    ├── formatter.py    - DB format output formatting
    ├── service.py      - Service layer helpers
    ├── flow.py         - Main onboarding flow
    └── start.py        - Start onboarding function
"""

# Re-export everything from the package for backward compatibility
# Re-export everything from the package for backward compatibility
from app.services.onboarding import (
    # Config
    ONBOARDING_FIELDS,
    DIETARY_PREFERENCE_FLAGS,
    ACTIVITY_MULTIPLIERS,
    TARGET_SPEED_RATES,
    # Utils
    safe_parse_json as _safe_parse_json,
    calculate_age as _calculate_age,
    convert_weight_to_kg as _convert_weight_to_kg,
    convert_height_to_cm as _convert_height_to_cm,
    # Validators
    validate_extracted_data as _validate_extracted_data,
    # Calculator
    calculate_metabolic_profile,
    # Formatter
    format_output_for_db,
    build_dietary_preferences as _build_dietary_preferences,
    get_default_dietary_preferences as _get_default_dietary_preferences,
    # Main flow
    onboarding,
    onboarding,
    start_onboarding,
)

# Internal helper exposed for testing
from app.services.onboarding.service import _extract_data_with_llm


# Legacy alias for backward compatibility
def calculate_macros(
    gender: str,
    weight_kg: float,
    height_cm: float,
    age: int,
    activity_level: str,
    goal: str,
):
    """Legacy function for backward compatibility."""
    return calculate_metabolic_profile(
        gender=gender,
        weight=weight_kg, weight_unit='kg',
        height=height_cm, height_unit='cm',
        age=age,
        activity_level=activity_level,
        goal=goal,
        target_weight=weight_kg, target_weight_unit='kg',
        target_speed='normal',
    )


__all__ = [
    'ONBOARDING_FIELDS',
    'DIETARY_PREFERENCE_FLAGS',
    'ACTIVITY_MULTIPLIERS',
    'TARGET_SPEED_RATES',
    'calculate_metabolic_profile',
    'calculate_macros',
    'format_output_for_db',
    'onboarding',
    'start_onboarding',
]
