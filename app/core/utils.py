"""Core utilities shared across modules."""

import json
import re
from typing import Any, Dict


def clean_json_response(response: str) -> str:
    """Extract JSON from potential markdown code blocks."""
    response = response.strip()
    if match := re.search(r"```(?:json)?(.*?)```", response, re.DOTALL):
        return match.group(1).strip()
    return response


def safe_parse_json(response: str) -> Dict[str, Any]:
    """Safely parse JSON with fallback strategies."""
    if not response or not isinstance(response, str):
        return {}
    
    response = response.strip()
    
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    # Try extracting from code blocks
    cleaned = clean_json_response(response)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    # Try regex fallback
    try:
        match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    
    return {}
