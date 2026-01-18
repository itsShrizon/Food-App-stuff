"""Receipt parsing functions using Google Gemini Vision API."""

import base64
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
import google.generativeai as genai

from receipt_parser.config import RECEIPT_PROMPT, BASE64_PROMPT

load_dotenv()


def _get_api_key(api_key: Optional[str] = None) -> str:
    """Get API key from parameter or environment."""
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY not found. Set in .env or pass as parameter.")
    return key


def _clean_response(response_text: str) -> str:
    """Clean markdown code blocks from response."""
    response_text = response_text.strip()
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])
        if response_text.startswith("json"):
            response_text = response_text[4:].strip()
    return response_text


def _validate_items(result: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure all items have required fields."""
    if "items" not in result:
        result["items"] = []
    
    for item in result["items"]:
        item.setdefault("name", "Unknown Item")
        item.setdefault("quantity", "1 unit")
        item.setdefault("price", "0.00")
    
    return result


def parse_receipt_image(
    image_path: str,
    *,
    api_key: Optional[str] = None,
    model: str = "gemini-2.5-flash",
) -> Dict[str, Any]:
    """Parse a receipt image and extract food items."""
    image_file = Path(image_path)
    if not image_file.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    key = _get_api_key(api_key)
    genai.configure(api_key=key)
    
    model_instance = genai.GenerativeModel(model)
    
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    try:
        response = model_instance.generate_content([
            RECEIPT_PROMPT, 
            {"mime_type": "image/jpeg", "data": image_data}
        ])
        
        cleaned = _clean_response(response.text)
        result = json.loads(cleaned)
        return _validate_items(result)
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON: {e}")
    except Exception as e:
        raise Exception(f"Error parsing receipt: {e}")


def parse_receipt_from_base64(
    base64_image: str,
    *,
    api_key: Optional[str] = None,
    model: str = "gemini-2.5-flash",
) -> Dict[str, Any]:
    """Parse a receipt from base64 encoded image data."""
    key = _get_api_key(api_key)
    genai.configure(api_key=key)
    
    model_instance = genai.GenerativeModel(model)
    
    try:
        image_data = base64.b64decode(base64_image)
    except Exception as e:
        raise ValueError(f"Invalid base64 image data: {e}")
    
    try:
        response = model_instance.generate_content([
            BASE64_PROMPT, 
            {"mime_type": "image/jpeg", "data": image_data}
        ])
        
        cleaned = _clean_response(response.text)
        result = json.loads(cleaned)
        return _validate_items(result)
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON: {e}")
    except Exception as e:
        raise Exception(f"Error parsing receipt: {e}")
