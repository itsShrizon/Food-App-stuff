"""Meal generation functions for single meals and daily plans."""

import json
from typing import Any, Dict, List, Optional

import app.core.llm as llm_module
from .config import (
    VALID_MEAL_TYPES,
    REQUIRED_USER_FIELDS,
    MEAL_GENERATION_SYSTEM_PROMPT,
    DAILY_MEAL_SYSTEM_PROMPT,
)
from .utils import (
    validate_user_info,
    build_user_context,
    build_previous_meals_context,
    clean_json_response,
    ensure_meal_schema,
)


def generate_meal(
    user_info: Dict[str, Any],
    meal_type: str,
    *,
    previous_meals: Optional[List[Dict[str, Any]]] = None,
    model: str = "gpt-4.1-nano",
    temperature: float = 0.7,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Generate a single personalized meal based on user's profile."""
    meal_type = meal_type.lower()
    if meal_type not in VALID_MEAL_TYPES:
        raise ValueError(f"Invalid meal_type: {meal_type}. Must be one of {VALID_MEAL_TYPES}")
    
    validate_user_info(user_info, REQUIRED_USER_FIELDS)
    
    user_context = build_user_context(user_info)
    previous_context = build_previous_meals_context(previous_meals or [])
    
    prompt = f"""{user_context}{previous_context}

Generate a {meal_type} meal that:
1. Aligns with {user_info['goal']} goal
2. Matches {user_info['activity_level']} activity level
3. Provides balanced nutrition
4. servings: How many servings, default 1 integer value

Return ONLY valid JSON."""
    
    try:
        response = llm_module.chatbot(
            user_message=prompt,
            system_prompt=MEAL_GENERATION_SYSTEM_PROMPT,
            model=model,
            temperature=temperature,
            **kwargs,
        )
        
        cleaned = clean_json_response(response)
        meal_data = json.loads(cleaned)
        return ensure_meal_schema(meal_data, meal_type)
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse meal JSON: {e}")
    except Exception as e:
        raise RuntimeError(f"Error generating meal: {e}")


def generate_day_meals(
    user_info: Dict[str, Any],
    *,
    previous_meals: Optional[List[Dict[str, Any]]] = None,
    model: str = "gpt-4.1-nano",
    temperature: float = 0.7,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Generate a complete daily meal plan (Breakfast, Snacks, Lunch, Dinner)."""
    validate_user_info(user_info, REQUIRED_USER_FIELDS)

    user_context = build_user_context(user_info)
    previous_context = build_previous_meals_context(previous_meals or [], max_items=20)

    prompt = f"""{user_context}{previous_context}

Generate a complete daily meal plan with Breakfast, Snacks, Lunch, Dinner.
Return ONLY valid JSON with keys: "breakfast", "snacks", "lunch", "dinner".
"""

    try:
        response = llm_module.chatbot(
            user_message=prompt,
            system_prompt=DAILY_MEAL_SYSTEM_PROMPT,
            model=model,
            temperature=temperature,
            **kwargs,
        )
        
        cleaned = clean_json_response(response)
        daily_plan = json.loads(cleaned)
        
        result = {}
        for meal_type in VALID_MEAL_TYPES:
            meal_data = daily_plan.get(meal_type, {})
            result[meal_type] = ensure_meal_schema(meal_data, meal_type)
            
        return result

    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse daily plan JSON: {e}")
    except Exception as e:
        raise RuntimeError(f"Error generating daily plan: {e}")
