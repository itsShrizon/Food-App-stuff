# Meal Generator API Documentation

## Overview

The Meal Generator module creates personalized meal plans based on user fitness profiles. It uses AI to generate meals aligned with fitness goals, activity levels, and nutritional requirements.

---

## Functions

### `generate_meal(user_info, meal_type, **kwargs)`

Generate a single personalized meal.

#### Input Parameters

**Required:**

- `user_info` (dict): User's fitness profile containing:
  - `gender` (str): "male", "female", or "others"
  - `date_of_birth` (str): Date in "YYYY-MM-DD" format
  - `current_height` (str): Height value (e.g., "175")
  - `current_weight` (str): Weight value (e.g., "75")
  - `current_weight_unit` (str): "kg" or "lbs"
  - `target_weight` (str): Target weight value
  - `target_weight_unit` (str): "kg" or "lbs"
  - `goal` (str): "lose weight", "maintain", or "gain weight"
  - `activity_level` (str): "sedentary", "light", "moderate", or "active"

- `meal_type` (str): Type of meal to generate
  - Valid values: `"Breakfast"`, `"Snacks"`, `"Lunch"`, `"Dinner"`

**Optional:**

- `previous_meals` (list): List of previously generated meals to avoid repetition
- `model` (str): OpenAI model name (default: "gpt-4o-mini")
- `temperature` (float): AI creativity level 0.0-1.0 (default: 0.7)

#### Output Format

Returns a dictionary with the following structure:

```python
{
    "meal_type": "Breakfast" | "Snacks" | "Lunch" | "Dinner",
    "meal_name": "Grilled Chicken Salad",  # Actual dish name
    "meal_description": "A healthy protein-rich salad with grilled chicken breast",
    "ingredients": [
        {
            "name": "Chicken breast",
            "amount": "150g"
        },
        {
            "name": "Mixed greens",
            "amount": "100g"
        },
        {
            "name": "Olive oil",
            "amount": "1 tablespoon"
        }
    ],
    "preparation_time": "20 minutes",
    "cooking_instructions": "Season chicken with salt and pepper. Grill for 6-8 minutes per side. Slice and serve over mixed greens with olive oil dressing.",
    "nutritional_info": {
        "calories": "320kcal",
        "protein": "35g",
        "carbohydrate": "8g",
        "fat": "15g"
    }
}
```

#### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `meal_type` | string | Category: Breakfast, Snacks, Lunch, or Dinner |
| `meal_name` | string | Specific dish name (e.g., "Chicken Fry", "Caesar Salad") |
| `meal_description` | string | Brief description of the meal |
| `ingredients` | array | List of ingredient objects with name and amount |
| `preparation_time` | string | Time needed to prepare (e.g., "20 minutes") |
| `cooking_instructions` | string | Step-by-step preparation instructions |
| `nutritional_info` | object | Caloric and macronutrient information |

#### Example Usage

```python
from meal_generator import generate_meal

# User profile
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

# Generate lunch meal
lunch = generate_meal(user_info, meal_type="Lunch")

# Access the results
print(f"Meal Type: {lunch['meal_type']}")  # "Lunch"
print(f"Meal Name: {lunch['meal_name']}")  # e.g., "Grilled Salmon Bowl"
print(f"Calories: {lunch['nutritional_info']['calories']}")
```

---

### `generate_daily_meal_plan(user_info, **kwargs)`

Generate a complete daily meal plan with all meal types.

#### Input Parameters

**Required:**

- `user_info` (dict): Same user profile as `generate_meal()`

**Optional:**

- `model` (str): OpenAI model name (default: "gpt-4o-mini")
- `temperature` (float): AI creativity level 0.0-1.0 (default: 0.7)

#### Output Format

Returns a dictionary with meal types as keys:

```python
{
    "Breakfast": {
        "meal_type": "Breakfast",
        "meal_name": "Oatmeal with Berries",
        # ... (same structure as single meal)
    },
    "Snacks": {
        "meal_type": "Snacks",
        "meal_name": "Greek Yogurt with Almonds",
        # ... (same structure as single meal)
    },
    "Lunch": {
        "meal_type": "Lunch",
        "meal_name": "Chicken Stir Fry",
        # ... (same structure as single meal)
    },
    "Dinner": {
        "meal_type": "Dinner",
        "meal_name": "Baked Salmon with Vegetables",
        # ... (same structure as single meal)
    }
}
```

#### Example Usage

```python
from meal_generator import generate_daily_meal_plan

# User profile
user_info = {
    "gender": "female",
    "date_of_birth": "1995-06-20",
    "current_height": "165",
    "current_weight": "65",
    "current_weight_unit": "kg",
    "target_weight": "60",
    "target_weight_unit": "kg",
    "goal": "lose weight",
    "activity_level": "light"
}

# Generate complete daily plan
daily_plan = generate_daily_meal_plan(user_info)

# Access meals
for meal_type, meal in daily_plan.items():
    print(f"{meal_type}: {meal['meal_name']}")
    print(f"  Calories: {meal['nutritional_info']['calories']}")

# Calculate total daily calories
total_calories = sum(
    int(''.join(filter(str.isdigit, meal['nutritional_info']['calories'])))
    for meal in daily_plan.values()
)
print(f"\nTotal Daily Calories: {total_calories}kcal")
```

---

## Key Distinctions

### `meal_type` vs `meal_name`

- **`meal_type`**: The meal category (Breakfast, Snacks, Lunch, Dinner)
  - Used as input parameter to specify when the meal is eaten
  - Standard values: `"Breakfast"`, `"Snacks"`, `"Lunch"`, `"Dinner"`

- **`meal_name`**: The actual dish name (e.g., "Chicken Fry", "Caesar Salad")
  - Generated by AI based on the recipe
  - Examples: "Grilled Chicken Salad", "Fried Rice", "Protein Smoothie"

**Example:**
```python
meal = generate_meal(user_info, meal_type="Dinner")
# Output:
# {
#     "meal_type": "Dinner",          # Category
#     "meal_name": "Chicken Fry",     # Actual dish
#     ...
# }
```

---

## Error Handling

### ValueError Exceptions

```python
# Invalid meal_type
try:
    meal = generate_meal(user_info, meal_type="Brunch")
except ValueError as e:
    # "Invalid meal_type: Brunch. Must be one of ['Breakfast', 'Snacks', 'Lunch', 'Dinner']"
    print(e)

# Missing required fields
try:
    incomplete_info = {"gender": "male"}
    meal = generate_meal(incomplete_info, meal_type="Lunch")
except ValueError as e:
    # "Missing required user_info fields: ['date_of_birth', 'current_height', ...]"
    print(e)
```

---

## Notes

1. **AI-Generated Content**: Meals are generated using AI and may vary each time
2. **Nutritional Accuracy**: Nutritional values are estimates based on AI calculations
3. **Variety**: Use `previous_meals` parameter to avoid repetitive meal suggestions
4. **Customization**: Adjust `temperature` parameter for more creative (higher) or consistent (lower) results
5. **API Key Required**: Ensure `OPENAI_API_KEY` is set in your `.env` file

---

## Complete Example

```python
from meal_generator import generate_meal, generate_daily_meal_plan

# User completes onboarding
user_profile = {
    "gender": "male",
    "date_of_birth": "1988-03-15",
    "current_height": "180",
    "current_weight": "85",
    "current_weight_unit": "kg",
    "target_weight": "78",
    "target_weight_unit": "kg",
    "goal": "lose weight",
    "activity_level": "moderate"
}

# Generate single meal
breakfast = generate_meal(user_profile, meal_type="Breakfast")
print(f"{breakfast['meal_name']}: {breakfast['nutritional_info']['calories']}")
# Output: "Scrambled Eggs with Avocado Toast: 380kcal"

# Generate full daily plan
plan = generate_daily_meal_plan(user_profile)
for meal_type, meal in plan.items():
    print(f"{meal_type}: {meal['meal_name']}")
# Output:
# Breakfast: Protein Oatmeal
# Snacks: Greek Yogurt with Berries
# Lunch: Grilled Chicken Salad
# Dinner: Baked Salmon with Quinoa
```
