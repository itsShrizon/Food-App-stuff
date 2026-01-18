"""
Meal Generator Module - Backward Compatible Facade.

This module re-exports from the meal_generator package for backward compatibility.
Actual implementation is in meal_generator/ package.
"""

from meal_generator import (
    generate_meal,
    generate_day_meals,
    generate_meal_plan,
    VALID_MEAL_TYPES,
    REQUIRED_USER_FIELDS,
)

# Re-export internal helpers for any legacy code that might use them
from meal_generator.utils import calculate_age as _calculate_age
from meal_generator.utils import ensure_meal_schema as _ensure_meal_schema

# Legacy prompts (for any code that imported these directly)
from meal_generator.config import MEAL_GENERATION_SYSTEM_PROMPT
from meal_generator.config import DAILY_MEAL_SYSTEM_PROMPT as DAILY_MEAL_GENERATION_SYSTEM_PROMPT

__all__ = [
    'generate_meal',
    'generate_day_meals',
    'generate_meal_plan',
    'VALID_MEAL_TYPES',
    'MEAL_GENERATION_SYSTEM_PROMPT',
    'DAILY_MEAL_GENERATION_SYSTEM_PROMPT',
]