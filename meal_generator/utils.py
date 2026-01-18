"""Utility functions for meal generation."""

from datetime import datetime
from typing import Any, Dict, List


def calculate_age(date_of_birth: str) -> int:
    """Calculate age from date of birth string."""
    try:
        dob = datetime.strptime(date_of_birth, "%Y-%m-%d")
        today = datetime.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except Exception:
        return 25
    
def parse_nutritional_value(value: Any) -> Dict[str, str]:
    """Parse nutritional value that could be string or dict format."""
    if isinstance(value, dict):
        return {
            "value": str(value.get("value", "0")),
            "unit": str(value.get("unit", ""))
        }
    # If it's a string like "0kcal" or "0g", try to extract value and unit
    if isinstance(value, str):
        import re
        match = re.match(r'([\d.]+)\s*(\w+)?', value)
        if match:
            return {
                "value": match.group(1),
                "unit": match.group(2) or ""
            }
    return {"value": "0", "unit": ""}

def ensure_meal_schema(meal_data: Dict[str, Any], fallback_meal_type: str) -> Dict[str, Any]:
    """Fill in any schema gaps returned by the LLM."""
    meal_data.setdefault('meal_type', fallback_meal_type)
    meal_data.setdefault('name', 'Untitled Meal')
    meal_data.setdefault('meal_description', 'No description provided.')
    meal_data.setdefault('prepare_time', 'N/A')
    meal_data.setdefault('cooking_instructions', 'N/A')
    meal_data.setdefault('source', 'ai')
    meal_data.setdefault('servings', 1)
    meal_data.setdefault('tags', [])

    # Parse nutritional info with new structure
    nutritional_info = meal_data.get('nutrients') or meal_data.get('nutritional_info') or {}
    meal_data['nutrients'] = {
        'calories': parse_nutritional_value(nutritional_info.get('calories', {'value': '0', 'unit': 'kcal'})),
        'protein': parse_nutritional_value(nutritional_info.get('protein', {'value': '0', 'unit': 'g'})),
        'carbs': parse_nutritional_value(nutritional_info.get('carbs', {'value': '0', 'unit': 'g'})),
        'fats': parse_nutritional_value(nutritional_info.get('fats', {'value': '0', 'unit': 'g'})),
    }

    # Remove old nutritional_info key if it exists
    meal_data.pop('nutritional_info', None)

    ingredients = meal_data.get('ingredients')
    if not isinstance(ingredients, list) or not ingredients:
        meal_data['ingredients'] = [
            {'name': 'Sample Ingredient', 'quantity': '1', 'unit': 'serving', 'nutritional_info': {}}
        ]

    return meal_data


def build_user_context(user_info: Dict[str, Any]) -> str:
    """Build user context string for prompts."""
    return f"""User Profile:
- Gender: {user_info['gender']}
- Age: {calculate_age(user_info['date_of_birth'])} years
- Height: {user_info['current_height']} cm
- Current Weight: {user_info['current_weight']} {user_info['current_weight_unit']}
- Target Weight: {user_info['target_weight']} {user_info['target_weight_unit']}
- Fitness Goal: {user_info['goal']}
- Activity Level: {user_info['activity_level']}
"""


def build_previous_meals_context(previous_meals: List[Dict[str, Any]], max_items: int = 12) -> str:
    """Build previous meals context to avoid repetition."""
    if not previous_meals:
        return ""
    recent = previous_meals[-max_items:]
    names = [m.get('name', 'Unknown') for m in recent]
    return f"\n\nRecent meals: {', '.join(names)}\nGenerate different meals for variety."


def validate_user_info(user_info: Dict[str, Any], required_fields: List[str]) -> None:
    """Validate that user_info contains required fields."""
    missing = [f for f in required_fields if f not in user_info]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")


def clean_json_response(response: str) -> str:
    """Clean markdown code blocks from JSON response."""
    response = response.strip()
    if response.startswith("```"):
        response = response.split("```")[1]
        if response.startswith("json"):
            response = response[4:]
    return response.strip()
