"""Metabolic profile calculator for onboarding."""

from typing import Any, Dict
import math
from .config import ACTIVITY_MULTIPLIERS, TARGET_SPEED_RATES
from .utils import convert_weight_to_kg, convert_height_to_cm


def calculate_metabolic_profile(
    gender: str,
    weight: float,
    weight_unit: str,
    height: float,
    height_unit: str,
    age: int,
    activity_level: str,
    goal: str,
    target_weight: float,
    target_weight_unit: str,
    target_speed: str = 'normal',
) -> Dict[str, Any]:
    """Calculate metabolic profile matching DB structure."""
    # Convert to standard units
    weight_kg = convert_weight_to_kg(weight, weight_unit)
    height_cm = convert_height_to_cm(height, height_unit)
    target_kg = convert_weight_to_kg(target_weight, target_weight_unit)
    
    # Failsafe bounds
    weight_kg = max(30, min(300, weight_kg)) if weight_kg > 0 else 70
    height_cm = max(100, min(250, height_cm)) if height_cm > 0 else 170
    age = max(10, min(100, age)) if age > 0 else 25
    
    # BMR (Mifflin-St Jeor)
    bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + (5 if gender == 'male' else -161)
    
    # TDEE
    tdee = bmr * ACTIVITY_MULTIPLIERS.get(activity_level, 1.375)
    
    # Goal adjustment
    if goal == 'lose_weight':
        daily_cal = tdee - 400
    elif goal == 'gain_weight':
        daily_cal = tdee + 350
    else:
        daily_cal = tdee
    
    daily_cal = max(daily_cal, 1200)
    
    # Macros
    protein = round(weight_kg * 1.8, 1)
    fats = round(daily_cal * 0.25 / 9, 1)
    carbs = round((daily_cal - protein * 4 - fats * 9) / 4, 1)
    carbs = max(carbs, 50)
    
    # Weeks to goal
    diff = abs(weight_kg - target_kg)
    rate = TARGET_SPEED_RATES.get(target_speed, 0.5)
    weeks = 0.0 if goal == 'maintain' or diff < 0.5 else round(diff / rate, 1)
    days = math.ceil(weeks * 7)
    
    return {
        'daily_calorie_target': round(daily_cal, 1),
        'protein_g': protein,
        'carbs_g': carbs,
        'fats_g': fats,
        'tdee': round(tdee, 1),
        'bmr': round(bmr, 1),
        'estimated_days_to_goal': days,
    }
