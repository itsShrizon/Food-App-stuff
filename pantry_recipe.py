"""
Pantry Recipe Module - Backward Compatible Facade.

This module re-exports from the pantry_recipe package for backward compatibility.
Actual implementation is in pantry_recipe/ package.
"""

from pantry_recipe import generate_pantry_recipes

__all__ = ['generate_pantry_recipes']

if __name__ == "__main__":
    import json
    
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
