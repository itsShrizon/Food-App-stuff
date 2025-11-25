# Fitness Onboarding Chatbot

AI-powered conversational onboarding using LangChain and OpenAI GPT-4o-mini for intelligent data extraction.

## Features

✅ **Natural Conversation** - Users can answer in any format (e.g., "5 foot 9 inch", "20 july 2000")
✅ **Smart Extraction** - GPT-4o-mini intelligently extracts and structures data from natural language
✅ **Multi-field Support** - Extracts multiple pieces of information from a single response
✅ **Progress Tracking** - Shows real-time progress of data collection
✅ **JSON Output** - Returns structured data ready for backend integration

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
