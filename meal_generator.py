"""Meal generation module using LLM for personalized nutrition plans."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

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

DAILY_MEAL_GENERATION_SYSTEM_PROMPT = """You are an expert nutritionist and meal planner. Generate a complete daily meal plan (Breakfast, Snacks, Lunch, Dinner) based on user's fitness goals and profile.

IMPORTANT RULES:
1. Generate meals that align with the user's fitness goal (lose_weight, maintain, gain_weight)
2. Consider activity level for calorie requirements
3. Ensure balanced macronutrients (protein, carbs, fats) across the day
4. Provide realistic portion sizes with proper units (g, ml, pieces, etc.)
5. Include diverse, accessible ingredients
6. Calculate accurate nutritional information
7. Avoid repeating meals from previous days if provided
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
  "Breakfast": {
    "meal_name": "...",
    "meal_description": "...",
    "ingredients": [
      {
        "name": "...",
        "quantity": "...",
        "unit": "...",
        "nutritional_info": { "calories": "...", "protein": "...", "carbohydrate": "...", "fat": "..." }
      }
    ],
    "preparation_time": "...",
    "cooking_instructions": "...",
    "nutritional_info": { "calories": "...", "protein": "...", "carbohydrate": "...", "fat": "..." }
  },
  "Snacks": { ... },
  "Lunch": { ... },
  "Dinner": { ... }
}
"""


def generate_meal(
    user_info: Dict[str, Any],
    meal_type: str,
    *,
    previous_meals: Optional[List[Dict[str, Any]]] = None,
    model: str = "gpt-4.1-nano",
    temperature: float = 0.7,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Generate a single personalized meal based on user's profile.
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
        # We take the last few meals to avoid immediate repetition context window overload
        recent_history = previous_meals[-12:] 
        previous_meals_names = [meal.get('meal_name', 'Unknown') for meal in recent_history]
        previous_meals_context = f"\n\nRecently generated meals: {', '.join(previous_meals_names)}\nPlease generate a different meal to ensure variety."
    
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


def generate_day_meals(
    user_info: Dict[str, Any],
    *,
    previous_meals: Optional[List[Dict[str, Any]]] = None,
    model: str = "gpt-4.1-nano",
    temperature: float = 0.7,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Generate a complete daily meal plan (Breakfast, Snacks, Lunch, Dinner).
    """
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

    # Add previous meals context
    previous_meals_context = ""
    if previous_meals:
        recent_history = previous_meals[-20:]
        previous_meals_names = [meal.get('meal_name', 'Unknown') for meal in recent_history]
        previous_meals_context = f"\n\nRecently generated meals: {', '.join(previous_meals_names)}\nPlease generate different meals to ensure variety."

    prompt = f"""{user_context}{previous_meals_context}

Generate a complete daily meal plan including Breakfast, Snacks, Lunch, and Dinner.
1. Align with {user_info['goal']} goal
2. Match {user_info['activity_level']} activity level
3. Balanced nutrition
4. Realistic and easy to prepare

Return ONLY a valid JSON object with keys: "Breakfast", "Snacks", "Lunch", "Dinner".
"""

    try:
        response = chatbot(
            user_message=prompt,
            system_prompt=DAILY_MEAL_GENERATION_SYSTEM_PROMPT,
            model=model,
            temperature=temperature,
            **kwargs,
        )
        
        # Clean markdown
        response = response.strip()
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        
        daily_plan = json.loads(response.strip())
        
        # Validate and clean up
        cleaned_plan = {}
        for meal_type in ["Breakfast", "Snacks", "Lunch", "Dinner"]:
            meal_data = daily_plan.get(meal_type, {})
            cleaned_meal = _ensure_meal_schema(meal_data, meal_type)
            cleaned_plan[meal_type] = cleaned_meal
            
        return cleaned_plan

    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse daily plan JSON: {e}. Response: {response}")
    except Exception as e:
        raise RuntimeError(f"Error generating daily plan: {e}")


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
    Generate a meal plan for a specific number of days, starting from today.
    
    Args:
        user_info: Dictionary containing user's profile information.
        duration_days: Number of days to generate (default: 1).
        model: OpenAI model to use.
        temperature: Model temperature.
        previous_meals: Optional list of previously generated meals to avoid repetition.
        **kwargs: Additional parameters for chatbot.
        
    Returns:
        Dictionary where keys are Dates (YYYY-MM-DD), and values are dictionaries
        containing "Breakfast", "Snacks", "Lunch", "Dinner".
    """
    if duration_days < 1:
        raise ValueError("duration_days must be at least 1")

    full_plan: Dict[str, Dict[str, Any]] = {}
    history_tracker = previous_meals[:] if previous_meals else []
    
    current_date = datetime.now()

    for i in range(duration_days):
        target_date = current_date + timedelta(days=i)
        day_label = target_date.strftime("%Y-%m-%d")
        
        try:
            daily_meals = generate_day_meals(
                user_info=user_info,
                previous_meals=history_tracker,
                model=model,
                temperature=temperature,
                **kwargs,
            )
            
            full_plan[day_label] = daily_meals
            
            for meal_type in ["Breakfast", "Snacks", "Lunch", "Dinner"]:
                if meal_type in daily_meals:
                    history_tracker.append(daily_meals[meal_type])
                    
        except Exception as e:
            raise RuntimeError(f"Failed to generate plan for {day_label}: {str(e)}")

    return full_plan


def _calculate_age(date_of_birth: str) -> int:
    """Calculate age from date of birth string."""
    from datetime import datetime as dt
    try:
        dob = dt.strptime(date_of_birth, "%Y-%m-%d")
        today = dt.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age
    except Exception:
        return 25  # Default age if parsing fails


def _ensure_meal_schema(meal_data: Dict[str, Any], fallback_meal_type: str) -> Dict[str, Any]:
    """Fill in any schema gaps returned by the LLM."""
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
                'quantity': '1',
                'unit': 'serving',
                'nutritional_info': {}
            }
        ]

    return meal_data