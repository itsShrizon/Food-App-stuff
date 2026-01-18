"""Utility functions for parsing and validation."""

import json
import re
from datetime import datetime
from typing import Any, Dict


def safe_parse_json(response: str) -> Dict[str, Any]:
    """Safely parse JSON from LLM response with fallback strategies."""
    if not response or not isinstance(response, str):
        return {}
    
    response = response.strip()
    
    # Try direct parsing
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    # Try extracting from markdown code blocks
    if "```" in response:
        try:
            parts = response.split("```")
            for part in parts[1::2]:
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                try:
                    return json.loads(part)
                except json.JSONDecodeError:
                    continue
        except Exception:
            pass
    
    # Try regex fallback
    try:
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception:
        pass
    
    return {}


def calculate_age(date_of_birth: str) -> int:
    """Calculate age from date of birth string. Returns default on error."""
    try:
        dob = datetime.strptime(date_of_birth, "%Y-%m-%d")
        today = datetime.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age if 0 < age < 120 else 25
    except Exception:
        return 25


def convert_weight_to_kg(weight: float, unit: str) -> float:
    """Convert weight to kg based on unit."""
    return weight * 0.453592 if unit == 'lb' else weight


def convert_height_to_cm(height: float, unit: str) -> float:
    """Convert height to cm based on unit."""
    return height * 2.54 if unit == 'in' else height
