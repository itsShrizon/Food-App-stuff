"""Receipt parser module using Google Gemini Vision API."""

import base64
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()


def parse_receipt_image(
    image_path: str,
    *,
    api_key: Optional[str] = None,
    model: str = "gemini-2.5-flash",
) -> Dict[str, Any]:
    """
    Parse a receipt image and extract food items with quantities and prices.
    
    Args:
        image_path: Path to the receipt image file (jpg, png, etc.)
        api_key: Google Gemini API key (defaults to GEMINI_API_KEY from .env)
        model: Gemini model to use (default: "gemini-2.5-flash")
        
    Returns:
        Dictionary containing:
            - items: List of food items with name, quantity, and price
            - total: Total amount (if found on receipt)
            - store_name: Name of store/supermarket (if found)
            - date: Purchase date (if found)
            - currency: Currency symbol or code (if found)
            
    Raises:
        FileNotFoundError: If image file doesn't exist
        ValueError: If API key is not provided
        Exception: If API call fails
        
    Example:
        >>> result = parse_receipt_image("receipt.jpg")
        >>> print(result['items'])
        [
            {"name": "Chicken Breast", "quantity": "1kg", "price": "12.99"},
            {"name": "Brown Rice", "quantity": "2kg", "price": "8.50"}
        ]
    """
    # Validate image path
    image_file = Path(image_path)
    if not image_file.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    # Get API key
    if api_key is None:
        api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found. Set it in .env file or pass as parameter.")
    
    # Configure Gemini
    genai.configure(api_key=api_key)
    
    # Create model
    model_instance = genai.GenerativeModel(model)
    
    # Read and encode image
    with open(image_path, 'rb') as img_file:
        image_data = img_file.read()
    
    # Create prompt for extraction
    prompt = """Analyze this receipt image and extract all food-related items purchased.

For each food item, extract:
- Item name (the product name)
- Quantity (amount purchased with unit like kg, lbs, pieces, bottles, etc.)
- Price (individual item price)

Also extract:
- Store name (if visible)
- Total amount (if visible)
- Purchase date (if visible)
- Currency (if visible)

Return ONLY a valid JSON object in this exact format:
{
  "store_name": "Store Name or null",
  "date": "YYYY-MM-DD or null",
  "currency": "$" or "USD" or null,
  "items": [
    {
      "name": "Item Name",
      "quantity": "amount with unit",
      "price": "price as string"
    }
  ],
  "total": "total amount or null"
}

IMPORTANT:
- Only include FOOD items (groceries, produce, meat, dairy, snacks, beverages, etc.)
- Exclude non-food items like bags, utensils, taxes, or service charges
- If quantity is not specified, use "1 unit" or "1 piece"
- Keep prices as strings to preserve formatting
- Return only the JSON object, no other text or markdown"""

    try:
        # Upload image and generate content
        response = model_instance.generate_content([prompt, {"mime_type": "image/jpeg", "data": image_data}])
        
        # Extract and clean response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])
            if response_text.startswith("json"):
                response_text = response_text[4:].strip()
        
        # Parse JSON
        result = json.loads(response_text)
        
        # Validate structure
        if "items" not in result:
            result["items"] = []
        
        # Ensure all items have required fields
        for item in result["items"]:
            if "name" not in item:
                item["name"] = "Unknown Item"
            if "quantity" not in item:
                item["quantity"] = "1 unit"
            if "price" not in item:
                item["price"] = "0.00"
        
        return result
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from Gemini response: {e}\nResponse: {response_text}")
    except Exception as e:
        raise Exception(f"Error parsing receipt with Gemini API: {e}")


def parse_receipt_from_base64(
    base64_image: str,
    *,
    api_key: Optional[str] = None,
    model: str = "gemini-2.5-flash",
) -> Dict[str, Any]:
    """
    Parse a receipt from base64 encoded image data.
    
    Args:
        base64_image: Base64 encoded image string
        api_key: Google Gemini API key (defaults to GEMINI_API_KEY from .env)
        model: Gemini model to use (default: "gemini-1.5-flash")
        
    Returns:
        Same format as parse_receipt_image()
        
    Example:
        >>> with open("receipt.jpg", "rb") as f:
        ...     b64_data = base64.b64encode(f.read()).decode()
        >>> result = parse_receipt_from_base64(b64_data)
    """
    # Get API key
    if api_key is None:
        api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found. Set it in .env file or pass as parameter.")
    
    # Configure Gemini
    genai.configure(api_key=api_key)
    
    # Create model
    model_instance = genai.GenerativeModel(model)
    
    # Decode base64
    try:
        image_data = base64.b64decode(base64_image)
    except Exception as e:
        raise ValueError(f"Invalid base64 image data: {e}")
    
    # Create prompt (same as above)
    prompt = """Analyze this receipt image and extract all food-related items purchased.

For each food item, extract:
- Item name (the product name)
- Quantity (amount purchased with unit like kg, lbs, pieces, bottles, etc.)
- Price (individual item price)

Also extract:
- Store name (if visible)
- Total amount (if visible)
- Purchase date (if visible)
- Currency (if visible)

Return ONLY a valid JSON object in this exact format:
{
  "store_name": "Store Name or null",
  "date": "YYYY-MM-DD or null",
  "currency": "$" or "USD" or null,
  "items": [
    {
      "name": "Item Name",
      "quantity": "amount with unit",
      "price": "price as string"
    }
  ],
  "total": "total amount or null"
}

IMPORTANT:
- Only include FOOD items (groceries, produce, meat, dairy, snacks, beverages, etc.)
- Exclude non-food items like bags, utensils, taxes, or service charges
- If quantity is not specified, use "1 unit" or "1 piece"
- Keep prices as strings to preserve formatting
- Return only the JSON object, no other text or markdown"""

    try:
        # Generate content
        response = model_instance.generate_content([prompt, {"mime_type": "image/jpeg", "data": image_data}])
        
        # Extract and clean response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])
            if response_text.startswith("json"):
                response_text = response_text[4:].strip()
        
        # Parse JSON
        result = json.loads(response_text)
        
        # Validate structure
        if "items" not in result:
            result["items"] = []
        
        # Ensure all items have required fields
        for item in result["items"]:
            if "name" not in item:
                item["name"] = "Unknown Item"
            if "quantity" not in item:
                item["quantity"] = "1 unit"
            if "price" not in item:
                item["price"] = "0.00"
        
        return result
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from Gemini response: {e}\nResponse: {response_text}")
    except Exception as e:
        raise Exception(f"Error parsing receipt with Gemini API: {e}")


def format_receipt_summary(receipt_data: Dict[str, Any]) -> str:
    """
    Format receipt data into a human-readable summary.
    
    Args:
        receipt_data: Dictionary returned from parse_receipt_image()
        
    Returns:
        Formatted string summary of the receipt
    """
    lines = []
    lines.append("=" * 60)
    lines.append("📄 RECEIPT SUMMARY")
    lines.append("=" * 60)
    
    # Store and date info
    if receipt_data.get("store_name"):
        lines.append(f"🏪 Store: {receipt_data['store_name']}")
    if receipt_data.get("date"):
        lines.append(f"📅 Date: {receipt_data['date']}")
    
    currency = receipt_data.get("currency", "$")
    
    lines.append("\n📦 ITEMS PURCHASED:")
    lines.append("-" * 60)
    
    # List items
    for i, item in enumerate(receipt_data.get("items", []), 1):
        name = item.get("name", "Unknown")
        quantity = item.get("quantity", "1 unit")
        price = item.get("price", "0.00")
        lines.append(f"{i}. {name}")
        lines.append(f"   Quantity: {quantity} | Price: {currency}{price}")
    
    # Total
    if receipt_data.get("total"):
        lines.append("-" * 60)
        lines.append(f"💰 TOTAL: {currency}{receipt_data['total']}")
    
    lines.append("=" * 60)
    
    return "\n".join(lines)



