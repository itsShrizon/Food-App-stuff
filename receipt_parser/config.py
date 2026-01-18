"""Configuration and prompts for receipt parsing."""

RECEIPT_PROMPT = """Analyze this receipt image and extract all food-related items purchased.

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
      "quantity": "amount",
      "unit": "unit of measurement",
      "price": "price as string",
      "nutritional_info": {
        "calories": {"value": "...", "unit": "kcal"},
        "protein": {"value": "...", "unit": "g"},
        "carbs": {"value": "...", "unit": "g"},
        "fats": {"value": "...", "unit": "g"}
      }
    }
  ],
  "total": "total amount or null"
}

IMPORTANT:
- Only include FOOD items (groceries, produce, meat, dairy, snacks, beverages)
- Exclude non-food items like bags, utensils, taxes
- If quantity not specified, use "1 unit" or "1 piece"
- Nutrition values should be estimated, not from receipt
- Return only the JSON object, no markdown
"""

BASE64_PROMPT = """Analyze this receipt image and extract all food-related items purchased.

For each food item, extract:
- Item name, Quantity, Price

Also extract: Store name, Total amount, Date, Currency

Return ONLY valid JSON:
{
  "store_name": "...", "date": "YYYY-MM-DD", "currency": "$",
  "items": [{"name": "...", "quantity": "...", "price": "..."}],
  "total": "..."
}

Only include FOOD items. Exclude non-food items.
"""
