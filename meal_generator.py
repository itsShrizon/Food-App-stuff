"""Meal generation module using LLM for personalized nutrition plans."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from LLM_shared import chatbot


MEAL_GENERATION_SYSTEM_PROMPT = """You are an expert nutritionist and meal planner. Generate personalized, healthy meals based on user's fitness goals and profile.

IMPORTANT RULES:
1. Generate meals that align with the user's fitness goal (lose_weight, maintain, gain_weight)
2. Consider activity level for calorie requirements
3. Ensure balanced macronutrients (protein, carbs, fats)
4. Provide realistic portion sizes with proper units (g, ml, pieces, etc.)
5. Include diverse, accessible ingredients
6. Calculate accurate nutritional information
7. Avoid repeating meals from previous_meals if provided
8. Return ONLY valid JSON, no explanations

Calorie Guidelines by Goal:
- lose_weight: caloric deficit (~300-500 kcal below maintenance)
- maintain: maintenance calories
- gain_weight: caloric surplus (~300-500 kcal above maintenance)

Activity Level Multipliers:
- sedentary: 1.2x BMR
- light: 1.375x BMR
- moderate: 1.55x BMR
- active: 1.725x BMR

Return format:
{
  "meal_type": "Breakfast" | "Snacks" | "Lunch" | "Dinner",
  "meal_name": "Actual meal name like 'Chicken Fry', 'Fried Rice', 'Caesar Salad'",
  "meal_description": "Brief description of the meal",
  "ingredients": [
    {
      "name": "Ingredient name",
      "quantity": "250" | "2" | "1",
      "unit": "g" | "ml" | "pieces" | "cups" | "etc.",
      "nutritional_info": {
        "calories": "100kcal",
        "protein": "5g",
        "carbohydrate": "12g",
        "fat": "3g"
      }
    }
  ],
  "preparation_time": "20 minutes",
  "cooking_instructions": "Brief instructions"
}
"""


def generate_meal(
    user_info: Dict[str, Any],
    meal_type: str,
    *,
    previous_meals: Optional[List[Dict[str, Any]]] = None,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Generate a personalized meal plan based on user's profile and fitness goals.
    
    Args:
        user_info: Dictionary containing user's profile information with fields:
            - gender: "male" | "female" | "others"
            - date_of_birth: "YYYY-MM-DD"
            - current_height: numeric (in cm)
            - current_height_unit: "cm"
            - current_weight: numeric
            - current_weight_unit: "kg" | "lbs"
            - target_weight: numeric
            - target_weight_unit: "kg" | "lbs"
            - goal: "lose_weight" | "maintain" | "gain_weight"
            - activity_level: "sedentary" | "light" | "moderate" | "active"
        meal_type: Type of meal to generate: "Breakfast", "Snacks", "Lunch", or "Dinner"
        previous_meals: Optional list of previously generated meals to avoid repetition
        model: OpenAI model to use (default: gpt-4o-mini)
        temperature: Model temperature (default: 0.7)
        **kwargs: Additional parameters for chatbot
        
    Returns:
        Dictionary containing:
            - meal_type: Type of meal ("Breakfast", "Snacks", "Lunch", "Dinner")
            - meal_name: Actual name of the dish (e.g., "Chicken Fry", "Caesar Salad")
            - meal_description: Brief description
            - ingredients: List of ingredients with amounts
            - preparation_time: Time needed to prepare
            - cooking_instructions: How to prepare the meal
            - nutritional_info: Calories, protein, carbs, fat
            
    Raises:
        ValueError: If meal_type is invalid or required user_info fields are missing
    """
    # Validate meal_type
    valid_meal_types = ["Breakfast", "Snacks", "Lunch", "Dinner"]
    if meal_type not in valid_meal_types:
        raise ValueError(f"Invalid meal_type: {meal_type}. Must be one of {valid_meal_types}")
    
    # Validate required fields
    required_fields = [
        'gender', 'date_of_birth', 'current_height', 'current_weight',
        'current_weight_unit', 'target_weight', 'target_weight_unit',
        'goal', 'activity_level'
    ]
    
    missing_fields = [field for field in required_fields if field not in user_info]
    if missing_fields:
        raise ValueError(f"Missing required user_info fields: {missing_fields}")
    
    # Build user context
    user_context = f"""
User Profile:
- Gender: {user_info['gender']}
- Age: {_calculate_age(user_info['date_of_birth'])} years
- Height: {user_info['current_height']} cm
- Current Weight: {user_info['current_weight']} {user_info['current_weight_unit']}
- Target Weight: {user_info['target_weight']} {user_info['target_weight_unit']}
- Fitness Goal: {user_info['goal']}
- Activity Level: {user_info['activity_level']}
"""
    
    # Add previous meals context if provided
    previous_meals_context = ""
    if previous_meals:
        previous_meals_names = [meal.get('meal_name', 'Unknown') for meal in previous_meals]
        previous_meals_context = f"\n\nPrevious meals today: {', '.join(previous_meals_names)}\nPlease generate a different meal to ensure variety."
    
    # Generate meal
    prompt = f"""{user_context}{previous_meals_context}

Generate a {meal_type} meal that:
1. Aligns with the user's {user_info['goal']} goal
2. Matches their {user_info['activity_level']} activity level
3. Provides balanced nutrition
4. Is realistic and easy to prepare

Return ONLY a valid JSON object with the meal details. No markdown, no explanations."""
    
    try:
        response = chatbot(
            user_message=prompt,
            system_prompt=MEAL_GENERATION_SYSTEM_PROMPT,
            model=model,
            temperature=temperature,
            **kwargs,
        )
        
        # Clean markdown code blocks if present
        response = response.strip()
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        
        meal_data = json.loads(response.strip())
        meal_data = _ensure_meal_schema(meal_data, meal_type)
        
        # Validate response structure
        required_keys = ['meal_type', 'meal_name', 'ingredients', 'nutritional_info']
        if not all(key in meal_data for key in required_keys):
            raise ValueError(f"Generated meal missing required keys: {required_keys}")
        
        return meal_data
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse meal JSON: {e}. Response: {response}")
    except Exception as e:
        raise RuntimeError(f"Error generating meal: {e}")


def generate_daily_meal_plan(
    user_info: Dict[str, Any],
    *,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    previous_meals: Optional[List[Dict[str, Any]]] = None,
    **kwargs: Any,
) -> Dict[str, Dict[str, Any]]:
    """
    Generate a complete daily meal plan with Breakfast, Snacks, Lunch, and Dinner.
    
    Args:
        user_info: Dictionary containing user's profile information
        model: OpenAI model to use (default: gpt-4o-mini)
        temperature: Model temperature (default: 0.7)
        previous_meals: Optional list of previously generated meals to avoid repetition
        **kwargs: Additional parameters for chatbot
        
    Returns:
        Dictionary with meal types as keys and meal details as values:
        {
            "Breakfast": {...},
            "Snacks": {...},
            "Lunch": {...},
            "Dinner": {...}
        }
    """
    meal_plan: Dict[str, Dict[str, Any]] = {}
    history = previous_meals[:] if previous_meals else []

    for meal_type in ["Breakfast", "Snacks", "Lunch", "Dinner"]:
        meal = generate_meal(
            user_info=user_info,
            meal_type=meal_type,
            previous_meals=history,
            model=model,
            temperature=temperature,
            **kwargs,
        )
        meal_plan[meal_type] = meal
        history.append(meal)

    return meal_plan, history


def _calculate_age(date_of_birth: str) -> int:
    """
    Calculate age from date of birth string.
    
    Args:
        date_of_birth: Date string in YYYY-MM-DD format
        
    Returns:
        Age in years
    """
    from datetime import datetime
    
    try:
        dob = datetime.strptime(date_of_birth, "%Y-%m-%d")
        today = datetime.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age
    except Exception:
        return 25  # Default age if parsing fails


def _ensure_meal_schema(meal_data: Dict[str, Any], fallback_meal_type: str) -> Dict[str, Any]:
    """Fill in any schema gaps returned by the LLM to keep downstream code safe."""
    meal_data.setdefault('meal_type', fallback_meal_type)
    meal_data.setdefault('meal_name', 'Untitled Meal')
    meal_data.setdefault('meal_description', 'No description provided.')
    meal_data.setdefault('preparation_time', 'N/A')
    meal_data.setdefault('cooking_instructions', 'N/A')

    nutritional_info = meal_data.get('nutritional_info') or {}
    meal_data['nutritional_info'] = {
        'calories': nutritional_info.get('calories', '0kcal'),
        'protein': nutritional_info.get('protein', '0g'),
        'carbohydrate': nutritional_info.get('carbohydrate', '0g'),
        'fat': nutritional_info.get('fat', '0g'),
    }

    ingredients = meal_data.get('ingredients')
    if not isinstance(ingredients, list) or not ingredients:
        meal_data['ingredients'] = [
            {
                'name': 'Sample Ingredient',
                'amount': '1 serving',
            }
        ]

    return meal_data


def generate_weekly_meal_plan(
    user_info: Dict[str, Any],
    *,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    previous_meals: Optional[List[Dict[str, Any]]] = None,
    **kwargs: Any,
) -> Dict[str, Dict[str, Any]]:
    """
    Generate a complete weekly meal plan with daily plans for Breakfast, Snacks, Lunch, and Dinner.
    
    Args:
        user_info: Dictionary containing user's profile information
        model: OpenAI model to use (default: gpt-4o-mini)
        temperature: Model temperature (default: 0.7)
        previous_meals: Optional list of previously generated meals to avoid repetition
        **kwargs: Additional parameters for chatbot
        
    Returns:
        Dictionary with days as keys and daily meal plans as values:
        {
            "Day 1": {"Breakfast": {...}, "Snacks": {...}, "Lunch": {...}, "Dinner": {...}},
            "Day 2": {...},
            ...
        }
    """
    weekly_history: List[Dict[str, Any]] = []
    weekly_plan: Dict[str, Dict[str, Dict[str, Any]]] = {}

    for day in range(7):
        plan, weekly_history = generate_daily_meal_plan(user_info, previous_meals=weekly_history)
        weekly_plan[f"Day {day + 1}"] = plan

    return weekly_plan