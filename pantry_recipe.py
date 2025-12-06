"""Pantry recipe generation module."""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from LLM_shared import chatbot

SYSTEM_PROMPT = """You are an expert chef and nutritionist.
Generate 5+ distinct, healthy recipes using provided pantry items, aligned with user's goals.
Return ONLY a valid JSON array.

Format:
[
  {
    "recipe_name": "string",
    "recipe_process": "string",
    "nutritional_values": {
      "calories": "string",
      "protein": "string",
      "carbohydrate": "string",
      "fat": "string"
    }
  }
]
"""


def _clean_json_response(response: str) -> str:
    """Extract JSON from potential markdown formatting."""
    response = response.strip()
    if match := re.search(r"```(?:json)?(.*?)```", response, re.DOTALL):
        return match.group(1).strip()
    return response


def generate_pantry_recipes(
    items: List[str],
    user_info: Dict[str, Any],
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    **kwargs: Any,
) -> List[Dict[str, Any]]:
    """Generate recipes based on pantry items and user profile."""
    if not items:
        raise ValueError("Item list cannot be empty.")

    user_details = "\n".join(
        f"- {k.replace('_', ' ').title()}: {v}" for k, v in sorted(user_info.items())
    )
    prompt = (
        f"User Profile:\n{user_details}\n\n"
        f"Pantry Items: {', '.join(items)}\n\n"
        "Generate at least 5 recipes aligned with the goal. Return JSON only."
    )

    try:
        raw_response = chatbot(
            user_message=prompt,
            system_prompt=SYSTEM_PROMPT,
            model=model,
            temperature=temperature,
            **kwargs,
        )

        json_str = _clean_json_response(raw_response)
        data = json.loads(json_str)

        recipes = data.get("recipes", data) if isinstance(data, dict) else data
        if not isinstance(recipes, list):
            raise ValueError("Output format invalid: expected a list of recipes.")
        if len(recipes) < 5:
            raise ValueError("Expected at least 5 recipes from the model.")

        return recipes

    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Recipe generation failed: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error: {e}") from e


if __name__ == "__main__":
    sample_user = {
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
    try:
        print(
            json.dumps(
                generate_pantry_recipes(["chicken", "rice", "broccoli"], sample_user),
                indent=2,
            )
        )
    except Exception as exc:
        print(f"Error: {exc}")
