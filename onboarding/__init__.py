"""Onboarding package - Layered architecture for user profile collection."""

# Config
from onboarding.config import (
    ONBOARDING_FIELDS,
    DIETARY_PREFERENCE_FLAGS,
    ACTIVITY_MULTIPLIERS,
    TARGET_SPEED_RATES,
)

# Utils
from onboarding.utils import (
    safe_parse_json,
    calculate_age,
    convert_weight_to_kg,
    convert_height_to_cm,
)

# Validators
from onboarding.validators import validate_extracted_data

# Calculator
from onboarding.calculator import calculate_metabolic_profile

# Formatter
from onboarding.formatter import (
    format_output_for_db,
    build_dietary_preferences,
    get_default_dietary_preferences,
)

# Main flow
from onboarding.flow import onboarding
from onboarding.start import start_onboarding


__all__ = [
    # Config
    'ONBOARDING_FIELDS',
    'DIETARY_PREFERENCE_FLAGS',
    'ACTIVITY_MULTIPLIERS',
    'TARGET_SPEED_RATES',
    # Utils
    'safe_parse_json',
    'calculate_age',
    'convert_weight_to_kg',
    'convert_height_to_cm',
    # Validators
    'validate_extracted_data',
    # Calculator
    'calculate_metabolic_profile',
    # Formatter
    'format_output_for_db',
    'build_dietary_preferences',
    'get_default_dietary_preferences',
    # Main flow
    'onboarding',
    'start_onboarding',
]
