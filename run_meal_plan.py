"""Separate module for running daily meal plan generation."""

from typing import Any, Dict
from meal_generator import generate_daily_meal_plan, generate_weekly_meal_plan
import json


def run(
    user_info: Dict[str, Any],
    model: str = "gpt-4o-mini",
    temperature: float = 0.1,
    days: int = 7,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Generate meal plans for the requested number of days (default 7).
    """
    if days <= 0:
        raise ValueError("days must be >= 1")

    if days == 1:
        plan, _ = generate_daily_meal_plan(
            user_info=user_info,
            model=model,
            temperature=temperature,
            **kwargs,
        )
        return plan

    return generate_weekly_meal_plan(
        user_info=user_info,
        model=model,
        temperature=temperature,
        **kwargs,
    )


user_info = {
    "gender": "male",
    "date_of_birth": "1990-01-01",
    "current_height": 180,
    "current_height_unit": "cm",
    "current_weight": 80,
    "current_weight_unit": "kg",
    "target_weight": 75,
    "target_weight_unit": "kg",
    "goal": "lose_weight",
    "activity_level": "moderate",
}

weekly_plan = run(user_info, days=7)
print(json.dumps(weekly_plan, indent=4))