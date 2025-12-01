"""Meal generation module using LLM for personalized nutrition plans."""

import json
from typing import Any, Dict, List, Optional

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
      "amount": "250g" | "2 pieces" | "1 cup"
    }
  ],
  "preparation_time": "20 minutes",
  "cooking_instructions": "Brief instructions",
  "nutritional_info": {
    "calories": "300kcal",
    "protein": "30g",
    "carbohydrate": "15g",
    "fat": "12g"
  }
}"""


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
    **kwargs: Any,
) -> Dict[str, Dict[str, Any]]:
    """
    Generate a complete daily meal plan with Breakfast, Snacks, Lunch, and Dinner.
    
    Args:
        user_info: Dictionary containing user's profile information
        model: OpenAI model to use (default: gpt-4o-mini)
        temperature: Model temperature (default: 0.7)
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
    meal_plan = {}
    previous_meals = []
    
    meal_types = ["Breakfast", "Snacks", "Lunch", "Dinner"]
    
    for meal_type in meal_types:
        meal = generate_meal(
            user_info=user_info,
            meal_type=meal_type,
            previous_meals=previous_meals,
            model=model,
            temperature=temperature,
            **kwargs,
        )
        meal_plan[meal_type] = meal
        previous_meals.append(meal)
    
    return meal_plan


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