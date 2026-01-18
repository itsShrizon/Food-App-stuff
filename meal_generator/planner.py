"""Multi-day meal planning functions."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .generator import generate_day_meals
from .config import VALID_MEAL_TYPES


def generate_meal_plan(
    user_info: Dict[str, Any],
    duration_days: int = 1,
    *,
    model: str = "gpt-4.1-nano",
    temperature: float = 0.7,
    previous_meals: Optional[List[Dict[str, Any]]] = None,
    **kwargs: Any,
) -> Dict[str, Dict[str, Any]]:
    """
    Generate a meal plan for multiple days.

    Args:
        user_info: User's profile information.
        duration_days: Number of days to generate.
        model: OpenAI model to use.
        temperature: Model temperature.
        previous_meals: Previously generated meals to avoid repetition.

    Returns:
        Dictionary with dates as keys (YYYY-MM-DD), values are daily meal plans.
    """
    if duration_days < 1:
        raise ValueError("duration_days must be at least 1")

    full_plan: Dict[str, Dict[str, Any]] = {}
    history = list(previous_meals) if previous_meals else []
    current_date = datetime.now()

    for i in range(duration_days):
        target_date = current_date + timedelta(days=i)
        day_label = target_date.strftime("%Y-%m-%d")

        try:
            daily_meals = generate_day_meals(
                user_info=user_info,
                previous_meals=history,
                model=model,
                temperature=temperature,
                **kwargs,
            )

            full_plan[day_label] = daily_meals

            # Update history for variety
            for meal_type in VALID_MEAL_TYPES:
                if meal_type in daily_meals:
                    history.append(daily_meals[meal_type])

        except Exception as e:
            raise RuntimeError(f"Failed to generate plan for {day_label}: {e}")

    return full_plan


def generate_meal_plan_list(
    user_info: Dict[str, Any],
    duration_days: int = 1,
    *,
    model: str = "gpt-4.1-nano",
    temperature: float = 0.7,
    previous_meals: Optional[List[Dict[str, Any]]] = None,
    **kwargs: Any,
) -> Dict[str, Dict[str, Any]]:
    """
    Generate a meal plan for multiple days.

    Args:
        user_info: User's profile information.
        duration_days: Number of days to generate.
        model: OpenAI model to use.
        temperature: Model temperature.
        previous_meals: Previously generated meals to avoid repetition.

    Returns:
        Dictionary with dates as keys (YYYY-MM-DD), values are daily meal plans.
    """
    if duration_days < 1:
        raise ValueError("duration_days must be at least 1")

    history = list(previous_meals) if previous_meals else []

    daily_meal_list = []

    for i in range(duration_days):
        try:
            daily_meals = generate_day_meals(
                user_info=user_info,
                previous_meals=history,
                model=model,
                temperature=temperature,
                **kwargs,
            )
            daily_meal_list.append(daily_meals)

            # Update history for variety
            for meal_type in VALID_MEAL_TYPES:
                if meal_type in daily_meals:
                    history.append(daily_meals[meal_type])

        except Exception as e:
            raise RuntimeError(f"Failed to generate plan for {i} days: {e}")

    return daily_meal_list
