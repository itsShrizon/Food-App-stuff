# Fitness Onboarding Chatbot

AI-powered conversational onboarding using LangChain and OpenAI GPT-4o-mini for intelligent data extraction.

## Features

✅ **Natural Conversation** - Users can answer in any format (e.g., "5 foot 9 inch", "20 july 2000")
✅ **Smart Extraction** - GPT-4o-mini intelligently extracts and structures data from natural language
✅ **Multi-field Support** - Extracts multiple pieces of information from a single response
✅ **Progress Tracking** - Shows real-time progress of data collection
✅ **JSON Output** - Returns structured data ready for backend integration
✅ **Receipt Parsing** - Extract food items from receipt images using Gemini Vision AI

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Create `.env` file:**
```bash
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
```

## Usage

### Run Interactive Onboarding

```bash
python run_onboarding.py
```

### Run Meal Generator

Generate personalized meals based on user fitness profile:

```bash
python run_meal_generator.py
```

Options:
- Generate single meal (Breakfast/Lunch/Snacks/Dinner)
- Generate complete daily meal plan
- Use sample profile for quick demo

**📖 See [MEAL_GENERATOR_API.md](MEAL_GENERATOR_API.md) for detailed API documentation**

### Parse Receipt Images

Extract food items from receipt images using Gemini Vision:

```bash
python receipt_parser.py receipt_image.jpg
```

**📖 See [RECEIPT_PARSER_API.md](RECEIPT_PARSER_API.md) for detailed API documentation**

### Use in Your Code

```python
from onboarding import start_onboarding, onboarding

# Start onboarding
result = start_onboarding()
print(result['message'])

# Process user responses
while not result['is_complete']:
    user_input = input("You: ")
    
    result = onboarding(
        user_message=user_input,
        conversation_history=result['conversation_history'],
        collected_data=result['collected_data']
    )
    
    print(f"Bot: {result['message']}")

# Get collected data
profile_data = result['collected_data']
print(json.dumps(profile_data, indent=2))
```

#### Meal Generation

```python
from meal_generator import generate_meal, generate_daily_meal_plan

# User profile from onboarding
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

# Generate a single meal
meal = generate_meal(user_info, meal_type="Lunch")
print(meal)

# Generate complete daily plan
daily_plan = generate_daily_meal_plan(user_info)
for meal_type, meal_data in daily_plan.items():
    print(f"{meal_type}: {meal_data['meal_name']}")
```

#### Receipt Parsing

```python
from receipt_parser import parse_receipt_image, format_receipt_summary

# Parse receipt image
receipt_data = parse_receipt_image("grocery_receipt.jpg")

# Display formatted summary
print(format_receipt_summary(receipt_data))

# Access extracted items
for item in receipt_data['items']:
    print(f"{item['name']}: {item['quantity']} - ${item['price']}")

# Example output:
# Chicken Breast: 1kg - $12.99
# Brown Rice: 2kg - $8.50
# Greek Yogurt: 4 cups - $6.99
```

## Collected Fields

- `gender`: male, female, others
- `date_of_birth`: YYYY-MM-DD format
- `current_height` + `current_height_unit`: numeric + (cm/inch)
- `target_height` + `target_height_unit`: numeric + (cm/inch)  
- `current_weight` + `current_weight_unit`: numeric + (kg/lbs)
- `target_weight` + `target_weight_unit`: numeric + (kg/lbs)
- `goal`: lose_weight, maintain, gain_weight
- `target_timeline_value` + `target_timeline_unit`: numeric + (days/weeks/months/years)
- `target_speed`: slow, normal, fast
- `activity_level`: sedentary, light, moderate, active

## How It Works

1. **Conversational Interface**: Users chat naturally with the bot
2. **LLM Extraction**: After each message, GPT-4o-mini analyzes the entire conversation and extracts structured data
3. **Smart Recognition**: Handles various formats:
   - "5 foot 9 inch" → 69 inches
   - "20 july 2000" → 2000-07-20
   - "90 kg" → weight: 90, unit: kg
4. **Completion Detection**: Automatically detects when all required fields are collected
5. **JSON Output**: Returns clean, structured data for backend storage

## Testing

```bash
# Run all tests
pytest test_onboarding.py -v

# Run specific test class
pytest test_onboarding.py::TestChatbot -v
```

## Example Conversation

```
Bot: Hello! 👋 Welcome to your fitness journey. Let's start with some basics.
     What's your gender, and when were you born?

You: I'm male, born on 20 july 2000

Bot: Great! Now, what's your current height and weight?

You: 5 foot 9 inch, 90 kg

Bot: Perfect! What's your fitness goal?

You: I want to maintain my weight over the next 20 months

Bot: And how would you describe your activity level?

You: sedentary

Bot: Thank you! I have all the information I need. Your profile is complete! 🎉

📋 Collected Profile Data (JSON):
{
  "gender": "male",
  "date_of_birth": "2000-07-20",
  "current_height": 69,
  "current_height_unit": "inch",
  "target_height": 69,
  "target_height_unit": "inch",
  "current_weight": 90,
  "current_weight_unit": "kg",
  "target_weight": 90,
  "target_weight_unit": "kg",
  "goal": "maintain",
  "target_timeline_value": 20,
  "target_timeline_unit": "months",
  "target_speed": "normal",
  "activity_level": "sedentary"
}
```

## Architecture

- **LLM_shared.py** - Reusable chatbot function with LangChain + OpenAI
- **onboarding.py** - Onboarding logic with intelligent extraction
- **run_onboarding.py** - Interactive CLI interface
- **test_onboarding.py** - Comprehensive test suite

## Dependencies

- `langchain-openai` - LangChain OpenAI integration
- `langchain-core` - Core LangChain functionality
- `openai` - OpenAI Python client  
- `python-dotenv` - Environment variable management
- `pytest` - Testing framework
