"""Pantry recipe generation functions."""

import json
import re
from typing import Any, Dict, List

from ..core.llm import chatbot
from .config import SYSTEM_PROMPT


def _clean_json_response(response: str) -> str:
    """Extract JSON from potential markdown formatting."""
    response = response.strip()
    if match := re.search(r"```(?:json)?(.*?)```", response, re.DOTALL):
        return match.group(1).strip()
    return response


def generate_pantry_recipes(
    items: List[str],
    user_info: Dict[str, Any],
    model: str = "gpt-4.1-mini",
    temperature: float = 0.7,
    **kwargs: Any,
) -> List[Dict[str, Any]]:
    """
    Generate recipes based on pantry items and user profile.
    
    Args:
        items: List of pantry item names.
        user_info: User profile information.
        model: LLM model to use.
        temperature: Model temperature.
        
    Returns:
        List of recipe dictionaries.
    """
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
