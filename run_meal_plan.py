"""Separate module for running daily meal plan generation."""

from typing import Any, Dict
import json
from .meal_generator import generate_meal_plan  # Updated import

def run(
    user_info: Dict[str, Any],
    model: str = "gpt-4.1-nano",
    temperature: float = 0.1,
    days: int = 2,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Generate meal plans for the requested number of days.
    """
    # The new generate_meal_plan function handles both 1 day and multiple days
    # seamlessly, returning a dictionary keyed by date (YYYY-MM-DD).
    return generate_meal_plan(
        user_info=user_info,
        duration_days=days,
        model=model,
        temperature=temperature,
        **kwargs,
    )


if __name__ == "__main__":
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

    # Example: Generating for 7 days
    weekly_plan = run(user_info, days=2)
    print(json.dumps(weekly_plan, indent=4))