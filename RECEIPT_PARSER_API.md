# Receipt Parser API Documentation

## Overview

The Receipt Parser module uses Google's Gemini Vision API to extract food items, quantities, and prices from receipt images. Perfect for tracking grocery purchases and food expenses.

---

## Installation

```bash
pip install google-generativeai==0.8.3
```

Make sure your `.env` file contains:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## Functions

### `parse_receipt_image(image_path, **kwargs)`

Parse a receipt image file and extract food items with details.

#### Input Parameters

**Required:**
- `image_path` (str): Path to receipt image file (supports jpg, png, jpeg, webp)

**Optional:**
- `api_key` (str): Google Gemini API key (defaults to `GEMINI_API_KEY` from .env)
- `model` (str): Gemini model to use (default: "gemini-1.5-flash")

#### Output Format

Returns a dictionary with the following structure:

```python
{
    "store_name": "Walmart" | None,
    "date": "2025-12-01" | None,
    "currency": "$" | "USD" | None,
    "items": [
        {
            "name": "Chicken Breast",
            "quantity": "1kg",
            "price": "12.99"
        },
        {
            "name": "Brown Rice",
            "quantity": "2kg",
            "price": "8.50"
        }
    ],
    "total": "45.67" | None
}
```

#### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `store_name` | string/null | Name of store or supermarket |
| `date` | string/null | Purchase date in YYYY-MM-DD format |
| `currency` | string/null | Currency symbol ($, €, £) or code (USD, EUR) |
| `items` | array | List of food items purchased |
| `items[].name` | string | Product name |
| `items[].quantity` | string | Amount with unit (kg, lbs, pieces, bottles) |
| `items[].price` | string | Item price as string |
| `total` | string/null | Total receipt amount |

#### Example Usage

```python
from receipt_parser import parse_receipt_image

# Parse a receipt image
result = parse_receipt_image("receipt.jpg")

# Access the data
print(f"Store: {result['store_name']}")
print(f"Total: ${result['total']}")

# List all food items
for item in result['items']:
    print(f"{item['name']}: {item['quantity']} - ${item['price']}")

# Output:
# Store: Whole Foods Market
# Total: $67.84
# Chicken Breast: 1.2kg - $15.99
# Broccoli: 500g - $3.49
# Greek Yogurt: 4 cups - $8.99
```

---

### `parse_receipt_from_base64(base64_image, **kwargs)`

Parse a receipt from base64 encoded image data.

#### Input Parameters

**Required:**
- `base64_image` (str): Base64 encoded image string

**Optional:**
- `api_key` (str): Google Gemini API key
- `model` (str): Gemini model to use

#### Output Format

Same as `parse_receipt_image()`

#### Example Usage

```python
import base64
from receipt_parser import parse_receipt_from_base64

# Encode image to base64
with open("receipt.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

# Parse receipt
result = parse_receipt_from_base64(image_data)
print(result['items'])
```

---

### `format_receipt_summary(receipt_data)`

Format receipt data into human-readable text summary.

#### Input Parameters

**Required:**
- `receipt_data` (dict): Dictionary returned from `parse_receipt_image()`

#### Returns

Formatted string with receipt details.

#### Example Usage

```python
from receipt_parser import parse_receipt_image, format_receipt_summary

# Parse and format
result = parse_receipt_image("receipt.jpg")
summary = format_receipt_summary(result)
print(summary)

# Output:
# ============================================================
# 📄 RECEIPT SUMMARY
# ============================================================
# 🏪 Store: Target
# 📅 Date: 2025-12-01
#
# 📦 ITEMS PURCHASED:
# ------------------------------------------------------------
# 1. Organic Eggs
#    Quantity: 12 pieces | Price: $5.99
# 2. Whole Milk
#    Quantity: 1 gallon | Price: $4.49
# ------------------------------------------------------------
# 💰 TOTAL: $10.48
# ============================================================
```

---

## Command Line Usage

You can run the receipt parser directly from command line:

```bash
# Parse a receipt image
python receipt_parser.py receipt.jpg

# Output will show both formatted summary and JSON
```

---

## Important Notes

### What Gets Extracted

✅ **Food Items Only:**
- Groceries (produce, meat, dairy, grains)
- Beverages (water, juice, soda)
- Snacks and packaged foods
- Frozen foods
- Condiments and spices

❌ **Excluded:**
- Non-food items (bags, utensils, household products)
- Service charges
- Taxes
- Tips

### Quantity Handling

- If quantity not visible: defaults to "1 unit" or "1 piece"
- Preserves original units: kg, lbs, oz, liters, pieces, bottles, etc.
- Converts to standard format when possible

### Price Format

- Prices kept as strings to preserve formatting (e.g., "12.99" not 12.99)
- Includes decimal points
- Currency extracted separately

---

## Integration Examples

### With Meal Planner

```python
from receipt_parser import parse_receipt_image
from meal_generator import generate_meal

# Parse receipt to see what user bought
receipt = parse_receipt_image("grocery_receipt.jpg")

# Extract ingredients user has
available_ingredients = [item['name'] for item in receipt['items']]

# Generate meals using those ingredients
user_info = {
    "gender": "male",
    "date_of_birth": "1990-01-15",
    "current_height": "175",
    "current_weight": "75",
    "current_weight_unit": "kg",
    "target_weight": "70",
    "target_weight_unit": "kg",
    "goal": "lose weight",
    "activity_level": "moderate"
}

meal = generate_meal(user_info, meal_type="Dinner")
print(f"Suggested meal: {meal['meal_name']}")
print(f"Available ingredients: {', '.join(available_ingredients)}")
```

### Track Food Expenses

```python
from receipt_parser import parse_receipt_image
import json

# Parse multiple receipts
receipts = ["receipt1.jpg", "receipt2.jpg", "receipt3.jpg"]
total_spent = 0.0

for receipt_path in receipts:
    data = parse_receipt_image(receipt_path)
    if data['total']:
        amount = float(data['total'])
        total_spent += amount
        print(f"{data['store_name']}: ${amount}")

print(f"\nTotal food expenses: ${total_spent:.2f}")
```

### Build Shopping History

```python
from receipt_parser import parse_receipt_image
import json
from datetime import datetime

# Parse and store
receipt_data = parse_receipt_image("receipt.jpg")

# Create shopping history entry
shopping_entry = {
    "id": datetime.now().isoformat(),
    "store": receipt_data['store_name'],
    "date": receipt_data['date'],
    "items": receipt_data['items'],
    "total": receipt_data['total']
}

# Save to database or file
with open("shopping_history.json", "a") as f:
    f.write(json.dumps(shopping_entry) + "\n")
```

---

## Error Handling

### Common Exceptions

```python
from receipt_parser import parse_receipt_image

# File not found
try:
    result = parse_receipt_image("nonexistent.jpg")
except FileNotFoundError as e:
    print(f"Image file not found: {e}")

# Missing API key
try:
    result = parse_receipt_image("receipt.jpg", api_key=None)
except ValueError as e:
    print(f"API key error: {e}")

# Invalid image or API error
try:
    result = parse_receipt_image("corrupted.jpg")
except Exception as e:
    print(f"Parsing error: {e}")
```

---

## Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- WebP (.webp)
- Other formats supported by Gemini Vision API

---

## Best Practices

1. **Image Quality:**
   - Use clear, well-lit photos
   - Ensure text is readable
   - Avoid shadows or glare

2. **Receipt Position:**
   - Keep receipt flat and straight
   - Capture entire receipt in frame
   - Avoid cutting off edges

3. **Error Handling:**
   - Always wrap API calls in try-except
   - Check for None values in results
   - Validate items array is not empty

4. **API Usage:**
   - Be mindful of API rate limits
   - Cache results when possible
   - Use appropriate model (flash for speed, pro for accuracy)

---

## Response Validation

Always validate the response before using:

```python
result = parse_receipt_image("receipt.jpg")

# Check if items were found
if not result['items']:
    print("No food items found on receipt")
else:
    print(f"Found {len(result['items'])} items")

# Validate required fields
for item in result['items']:
    if not item.get('name'):
        print(f"Warning: Item missing name")
    if not item.get('price'):
        print(f"Warning: {item['name']} missing price")
```

---

## Complete Example

```python
from receipt_parser import parse_receipt_image, format_receipt_summary
import json

def process_receipt(image_path):
    """Process a receipt and display results."""
    try:
        # Parse receipt
        print(f"🔍 Processing {image_path}...")
        result = parse_receipt_image(image_path)
        
        # Display formatted summary
        print(format_receipt_summary(result))
        
        # Save JSON for database
        output_file = image_path.replace('.jpg', '_data.json')
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n✅ Data saved to {output_file}")
        
        # Calculate statistics
        total_items = len(result['items'])
        avg_price = sum(float(item['price']) for item in result['items']) / total_items
        
        print(f"\n📊 Statistics:")
        print(f"   Items: {total_items}")
        print(f"   Average price: ${avg_price:.2f}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# Use it
if __name__ == "__main__":
    process_receipt("grocery_receipt.jpg")
```

---

## Model Options

| Model | Speed | Accuracy | Cost | Use Case |
|-------|-------|----------|------|----------|
| gemini-1.5-flash | ⚡ Fast | Good | 💰 Low | Quick parsing, high volume |
| gemini-1.5-pro | 🐢 Slower | Better | 💰💰 Higher | Complex receipts, better accuracy |

```python
# Use flash for speed (default)
result = parse_receipt_image("receipt.jpg", model="gemini-1.5-flash")

# Use pro for accuracy
result = parse_receipt_image("receipt.jpg", model="gemini-1.5-pro")
```
