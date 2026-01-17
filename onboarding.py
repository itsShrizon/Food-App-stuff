"""Onboarding module for conversational user profile collection with macro recommendations."""

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from LLM_shared import chatbot


# Core required fields for onboarding
ONBOARDING_FIELDS = (
    'gender', 'date_of_birth',
    'current_height', 
    'current_weight', 
    'target_weight', 
    'goal', 
    'activity_level',
)

# Optional fields collected after macro confirmation
OPTIONAL_FIELDS = (
    'dietary_preference',  # vegan, vegetarian, pescatarian, keto, none, etc.
    'allergies',           # list of allergies to avoid
    'extra_notes',         # any additional preferences
)

# Activity level multipliers for TDEE calculation
ACTIVITY_MULTIPLIERS = {
    'sedentary': 1.2,
    'light': 1.375,
    'moderate': 1.55,
    'active': 1.725,
}

EXTRACTION_SYSTEM_PROMPT = """You are a data extraction AI. Extract fitness onboarding information from the conversation.

Required fields to extract:
- gender: male, female, or others
- date_of_birth: YYYY-MM-DD format
- current_height: numeric value and unit
- current_weight: numeric value and unit
- target_weight: numeric value and unit
- goal: "lose weight", "maintain", or "gain weight" 
- activity_level: "sedentary", "light", "moderate", or "active"
- dietary_preference: "vegan", "vegetarian", "pescatarian", "keto", "none", or specific preference
- allergies: list of food allergies (e.g., "nuts, dairy, gluten") or "none"
- extra_notes: any additional preferences or notes
- macros_confirmed: true if user confirmed the recommended macros

IMPORTANT RULES:
1. Extract ALL information mentioned in the conversation
2. Convert dates to YYYY-MM-DD format (e.g., "20 july 2000" → "2000-07-20")
3. Convert heights: feet/inches to inches (e.g., "5 foot 9 inch" → 69 inches, unit: "inch")
4. If target_speed not mentioned, default to "normal"
5. Only return fields that have been mentioned or can be inferred
6. Return ONLY valid JSON, no explanations
7. If user says "yes", "ok", "sounds good" to macros, set macros_confirmed: true

Return format:
{
  "field_name": "extracted_value"
}"""

CONVERSATION_SYSTEM_PROMPT = """You are a friendly AI fitness coach helping with onboarding. Have a natural, warm conversation to collect user information.

CURRENT STATE:
- Collected fields: {collected_fields}
- Missing required fields: {missing_fields}
- Macros calculated: {macros_calculated}
- Macros confirmed: {macros_confirmed}

{macro_info}

CONVERSATION FLOW:
1. First collect: gender, age/date_of_birth, height, weight, activity level, goal weight
2. After goal weight → Show recommended macros and ask if they're happy with them
3. After macro confirmation → Ask about dietary preferences, allergies, extras
4. When all done → Thank them and confirm profile is complete

RULES:
1. Be conversational and friendly - DON'T sound like a form
2. Ask one or two questions at a time
3. When showing macros, present them clearly and ask for confirmation
4. If user wants to adjust macros, help them understand the trade-offs
5. Keep responses brief and engaging
6. Use emojis sparingly for friendliness

Be natural and conversational!"""


def _safe_parse_json(response: str) -> Dict[str, Any]:
    """
    Safely parse JSON from LLM response with multiple fallback strategies.
    
    Failsafe against malformed JSON from AI hallucination.
    """
    if not response or not isinstance(response, str):
        return {}
    
    response = response.strip()
    
    # Try direct parsing first
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    # Try extracting JSON from markdown code blocks
    if "```" in response:
        try:
            # Extract content between code blocks
            parts = response.split("```")
            for part in parts[1::2]:  # Get odd-indexed parts (inside code blocks)
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                try:
                    return json.loads(part)
                except json.JSONDecodeError:
                    continue
        except Exception:
            pass
    
    # Try to find JSON-like content with regex
    try:
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception:
        pass
    
    # Return empty dict as final fallback
    return {}


def _validate_extracted_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and sanitize extracted data to prevent hallucination issues.
    
    Failsafe: ensures only valid values are accepted.
    """
    validated = {}
    
    # Validate gender
    if 'gender' in data:
        gender = str(data['gender']).lower().strip()
        if gender in ('male', 'female', 'others', 'other', 'm', 'f'):
            if gender == 'm':
                gender = 'male'
            elif gender == 'f':
                gender = 'female'
            elif gender == 'other':
                gender = 'others'
            validated['gender'] = gender
    
    # Validate date_of_birth
    if 'date_of_birth' in data:
        dob = str(data['date_of_birth']).strip()
        try:
            # Try parsing the date
            datetime.strptime(dob, "%Y-%m-%d")
            validated['date_of_birth'] = dob
        except ValueError:
            pass  # Invalid date format, skip
    
    # Validate activity_level
    if 'activity_level' in data:
        level = str(data['activity_level']).lower().strip()
        if level in ACTIVITY_MULTIPLIERS:
            validated['activity_level'] = level
    
    # Validate goal
    if 'goal' in data:
        goal = str(data['goal']).lower().strip()
        valid_goals = ('lose weight', 'maintain', 'gain weight', 'lose', 'gain', 'bulk', 'cut')
        if goal in valid_goals:
            if goal in ('lose', 'cut'):
                goal = 'lose weight'
            elif goal in ('gain', 'bulk'):
                goal = 'gain weight'
            validated['goal'] = goal
    
    # Validate numeric fields (heights, weights)
    numeric_fields = ['current_height', 'current_weight', 'target_weight']
    for field in numeric_fields:
        if field in data:
            value = data[field]
            # Allow string values with units like "180 cm" or "75 kg"
            if value is not None:
                validated[field] = str(value).strip()
    
    # Validate optional fields (less strict)
    if 'dietary_preference' in data and data['dietary_preference']:
        validated['dietary_preference'] = str(data['dietary_preference']).strip()
    
    if 'allergies' in data and data['allergies']:
        validated['allergies'] = str(data['allergies']).strip()
    
    if 'extra_notes' in data and data['extra_notes']:
        validated['extra_notes'] = str(data['extra_notes']).strip()
    
    if 'macros_confirmed' in data:
        # Accept various confirmation signals
        val = data['macros_confirmed']
        if isinstance(val, bool):
            validated['macros_confirmed'] = val
        elif isinstance(val, str):
            validated['macros_confirmed'] = val.lower() in ('true', 'yes', 'ok', 'confirmed')
    
    return validated


def calculate_macros(
    gender: str,
    weight_kg: float,
    height_cm: float,
    age: int,
    activity_level: str,
    goal: str,
) -> Dict[str, Any]:
    """
    Calculate recommended daily macros using Mifflin-St Jeor equation.
    
    Failsafe: Uses conservative defaults if inputs are invalid.
    
    Args:
        gender: 'male', 'female', or 'others'
        weight_kg: Weight in kilograms
        height_cm: Height in centimeters
        age: Age in years
        activity_level: 'sedentary', 'light', 'moderate', or 'active'
        goal: 'lose weight', 'maintain', or 'gain weight'
        
    Returns:
        Dictionary with calories, protein, carbs, fat recommendations
    """
    # Failsafe: validate and set defaults
    try:
        weight_kg = float(weight_kg)
        if weight_kg <= 0 or weight_kg > 500:
            weight_kg = 70  # Default
    except (TypeError, ValueError):
        weight_kg = 70
    
    try:
        height_cm = float(height_cm)
        if height_cm <= 0 or height_cm > 300:
            height_cm = 170  # Default
    except (TypeError, ValueError):
        height_cm = 170
    
    try:
        age = int(age)
        if age <= 0 or age > 120:
            age = 25  # Default
    except (TypeError, ValueError):
        age = 25
    
    # Calculate BMR using Mifflin-St Jeor equation
    if gender == 'male':
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:  # female or others
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    
    # Apply activity multiplier
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.375)  # Default to light
    tdee = bmr * multiplier
    
    # Adjust for goal
    if goal == 'lose weight':
        calories = tdee - 400  # Moderate deficit
    elif goal == 'gain weight':
        calories = tdee + 350  # Moderate surplus
    else:  # maintain
        calories = tdee
    
    # Ensure minimum calories
    calories = max(calories, 1200)
    
    # Calculate macros (moderate protein, balanced approach)
    protein_g = round(weight_kg * 1.8)  # 1.8g per kg bodyweight
    fat_g = round(calories * 0.25 / 9)  # 25% of calories from fat
    carbs_g = round((calories - (protein_g * 4 + fat_g * 9)) / 4)  # Remaining from carbs
    
    # Ensure non-negative
    carbs_g = max(carbs_g, 50)
    
    return {
        'calories': round(calories),
        'protein_g': protein_g,
        'carbs_g': carbs_g,
        'fat_g': fat_g,
        'bmr': round(bmr),
        'tdee': round(tdee),
    }


def _parse_weight_to_kg(weight_str: str) -> float:
    """Convert weight string to kg. Failsafe with default."""
    try:
        weight_str = str(weight_str).lower().strip()
        # Extract number
        num_match = re.search(r'[\d.]+', weight_str)
        if not num_match:
            return 70.0  # Default
        
        value = float(num_match.group())
        
        # Check for unit
        if 'lb' in weight_str or 'pound' in weight_str:
            return value * 0.453592  # lbs to kg
        return value  # Assume kg
    except Exception:
        return 70.0


def _parse_height_to_cm(height_str: str) -> float:
    """Convert height string to cm. Failsafe with default."""
    try:
        height_str = str(height_str).lower().strip()
        
        # Check for feet/inches format
        if 'foot' in height_str or 'feet' in height_str or "'" in height_str:
            # Try to extract feet and inches
            feet_match = re.search(r'(\d+)\s*(?:foot|feet|ft|\')', height_str)
            inch_match = re.search(r'(\d+)\s*(?:inch|inches|in|")', height_str)
            
            feet = float(feet_match.group(1)) if feet_match else 0
            inches = float(inch_match.group(1)) if inch_match else 0
            
            total_inches = feet * 12 + inches
            return total_inches * 2.54  # inches to cm
        
        # Extract number
        num_match = re.search(r'[\d.]+', height_str)
        if not num_match:
            return 170.0  # Default
        
        value = float(num_match.group())
        
        # If value seems like inches (< 100), convert
        if value < 100:
            return value * 2.54
        return value  # Assume cm
    except Exception:
        return 170.0


def _calculate_age(date_of_birth: str) -> int:
    """Calculate age from date of birth string. Failsafe with default."""
    try:
        dob = datetime.strptime(date_of_birth, "%Y-%m-%d")
        today = datetime.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age <= 0 or age > 120:
            return 25
        return age
    except Exception:
        return 25


def _extract_data_with_llm(
    conversation_history: List[Dict[str, str]],
    model: str = "gpt-4.1-nano",
) -> Dict[str, Any]:
    """
    Use LLM to intelligently extract all data from conversation.
    
    Failsafe: wrapped in try-catch with validation.
    """
    # Build conversation context
    conversation_text = "\n".join([
        f"{msg['role']}: {msg['content']}" 
        for msg in conversation_history
    ])
    
    extraction_prompt = f"""Extract fitness onboarding data from this conversation:

{conversation_text}

Return ONLY a JSON object with extracted fields. No other text."""
    
    try:
        response = chatbot(
            user_message=extraction_prompt,
            system_prompt=EXTRACTION_SYSTEM_PROMPT,
            model=model,
            temperature=0.0,  # Low temperature for consistent extraction
        )
        
        # Parse with failsafe
        extracted_data = _safe_parse_json(response)
        
        # Validate extracted data
        validated_data = _validate_extracted_data(extracted_data)
        
        return validated_data
        
    except Exception as e:
        print(f"Extraction error (failsafe activated): {e}")
        return {}


def onboarding(
    user_message: str,
    *,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    collected_data: Optional[Dict[str, Any]] = None,
    model: str = "gpt-4.1-nano",
    temperature: float = 0.1,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Process user response during onboarding and collect profile data.
    
    Includes macro recommendation after goal weight collection.
    Failsafe mechanisms prevent AI hallucination from breaking the flow.
    
    Args:
        user_message: User's response to the current question
        conversation_history: List of previous messages
        collected_data: Dictionary of already collected profile data
        model: OpenAI model to use
        temperature: Model temperature
        **kwargs: Additional parameters for chatbot
        
    Returns:
        Dictionary containing:
            - message: Bot's response/next question
            - conversation_history: Updated conversation history
            - collected_data: Updated collected profile data
            - is_complete: Boolean indicating if onboarding is complete
            - next_field: Next field to collect (if not complete)
            - recommended_macros: Calculated macros (if available)
    """
    # Initialize with failsafe
    conversation_history = list(conversation_history or [])
    collected_data = dict(collected_data or {})
    
    # Add user message to history
    conversation_history.append({"role": "user", "content": user_message})
    
    # Use LLM to extract data from entire conversation (with failsafe)
    try:
        extracted_data = _extract_data_with_llm(conversation_history, model=model)
    except Exception:
        extracted_data = {}
    
    # Update collected data with newly extracted info (only valid fields)
    all_fields = ONBOARDING_FIELDS + OPTIONAL_FIELDS + ('macros_confirmed',)
    for field, value in extracted_data.items():
        if field in all_fields and value:
            collected_data[field] = value
    
    # Check if we have enough data to calculate macros
    macros_calculated = 'recommended_macros' in collected_data
    macros_confirmed = collected_data.get('macros_confirmed', False)
    
    # Calculate macros if we have the required fields but haven't yet
    required_for_macros = ['gender', 'date_of_birth', 'current_height', 'current_weight', 
                          'activity_level', 'goal']
    have_all_for_macros = all(f in collected_data for f in required_for_macros)
    
    if have_all_for_macros and not macros_calculated:
        try:
            weight_kg = _parse_weight_to_kg(collected_data['current_weight'])
            height_cm = _parse_height_to_cm(collected_data['current_height'])
            age = _calculate_age(collected_data['date_of_birth'])
            
            macros = calculate_macros(
                gender=collected_data['gender'],
                weight_kg=weight_kg,
                height_cm=height_cm,
                age=age,
                activity_level=collected_data['activity_level'],
                goal=collected_data['goal'],
            )
            collected_data['recommended_macros'] = macros
            macros_calculated = True
        except Exception as e:
            print(f"Macro calculation error (failsafe): {e}")
            # Continue without macros rather than failing
    
    # Determine missing required fields
    missing_fields = [f for f in ONBOARDING_FIELDS if f not in collected_data]
    
    # Check for optional fields after macros confirmed
    missing_optional = []
    if macros_confirmed and not missing_fields:
        missing_optional = [f for f in OPTIONAL_FIELDS if f not in collected_data]
    
    # Check if onboarding is complete
    # Complete when: all required fields + macros confirmed + (optional fields asked or skipped)
    is_complete = (
        len(missing_fields) == 0 and 
        macros_confirmed and
        (len(missing_optional) == 0 or collected_data.get('optional_skipped', False))
    )
    
    # If user says "skip" or "no allergies" etc., mark optional as done
    skip_keywords = ['skip', 'none', 'no ', 'nothing', "don't have", "dont have"]
    if any(kw in user_message.lower() for kw in skip_keywords):
        if not missing_fields and macros_confirmed:
            collected_data['optional_skipped'] = True
            is_complete = True
    
    if is_complete:
        final_message = "Thank you! I have all the information I need. Your profile is complete! 🎉\n\n"
        
        if 'recommended_macros' in collected_data:
            macros = collected_data['recommended_macros']
            final_message += f"**Your Daily Targets:**\n"
            final_message += f"• Calories: {macros['calories']} kcal\n"
            final_message += f"• Protein: {macros['protein_g']}g\n"
            final_message += f"• Carbs: {macros['carbs_g']}g\n"
            final_message += f"• Fat: {macros['fat_g']}g\n"
        
        conversation_history.append({"role": "assistant", "content": final_message})
        
        return {
            "message": final_message,
            "conversation_history": conversation_history,
            "collected_data": collected_data,
            "is_complete": True,
            "next_field": None,
            "recommended_macros": collected_data.get('recommended_macros'),
        }
    
    # Build context for conversation
    collected_fields_str = ", ".join(collected_data.keys()) if collected_data else "none"
    missing_fields_str = ", ".join(missing_fields) if missing_fields else "none"
    
    # Build macro info for system prompt
    macro_info = ""
    if macros_calculated and not macros_confirmed:
        macros = collected_data['recommended_macros']
        macro_info = f"""
IMPORTANT: Show the user their recommended macros and ask if they're happy with them:
- Calories: {macros['calories']} kcal/day
- Protein: {macros['protein_g']}g
- Carbs: {macros['carbs_g']}g  
- Fat: {macros['fat_g']}g

Ask: "Are you happy with these recommendations, or would you like to adjust them?"
"""
    elif macros_confirmed and missing_optional:
        macro_info = f"Macros confirmed! Now ask about: {', '.join(missing_optional)}"
    
    system_prompt = CONVERSATION_SYSTEM_PROMPT.format(
        collected_fields=collected_fields_str,
        missing_fields=missing_fields_str,
        macros_calculated=macros_calculated,
        macros_confirmed=macros_confirmed,
        macro_info=macro_info,
    )
    
    # Generate bot response with failsafe
    try:
        bot_response = chatbot(
            user_message=f"User said: '{user_message}'. Respond naturally and continue the onboarding.",
            system_prompt=system_prompt,
            conversation_history=conversation_history[:-1],  # Exclude last message
            model=model,
            temperature=temperature,
            **kwargs,
        )
    except Exception as e:
        # Failsafe: provide a generic recovery response
        print(f"Chatbot error (failsafe): {e}")
        if missing_fields:
            bot_response = f"I'd love to hear more! Could you tell me about your {missing_fields[0].replace('_', ' ')}?"
        elif macros_calculated and not macros_confirmed:
            macros = collected_data['recommended_macros']
            bot_response = f"Based on your profile, I recommend {macros['calories']} calories daily. Does that sound good?"
        else:
            bot_response = "Thanks! Is there anything else you'd like to share about your preferences?"
    
    # Add bot response to history
    conversation_history.append({"role": "assistant", "content": bot_response})
    
    return {
        "message": bot_response,
        "conversation_history": conversation_history,
        "collected_data": collected_data,
        "is_complete": False,
        "next_field": missing_fields[0] if missing_fields else (missing_optional[0] if missing_optional else None),
        "recommended_macros": collected_data.get('recommended_macros'),
    }


def start_onboarding(
    *,
    model: str = "gpt-4.1-nano",
    temperature: float = 0.7,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Start a new onboarding conversation.

    Args:
        model: OpenAI model identifier. Defaults to "gpt-4.1-nano".
        temperature: Sampling temperature. Defaults to 0.7.
        **kwargs: Additional arguments passed to chatbot function.

    Returns:
        Dict containing initial onboarding state with welcome message.
    """
    missing_fields_str = ", ".join(ONBOARDING_FIELDS)
    
    system_prompt = CONVERSATION_SYSTEM_PROMPT.format(
        collected_fields="none",
        missing_fields=missing_fields_str,
        macros_calculated=False,
        macros_confirmed=False,
        macro_info="",
    )

    try:
        welcome_message = chatbot(
            user_message="Start the fitness onboarding. Give a warm, friendly welcome and ask about basic info (gender, age) in a natural conversational way. Keep it brief!",
            system_prompt=system_prompt,
            model=model,
            temperature=temperature,
            **kwargs,
        )
    except Exception as e:
        # Failsafe welcome message
        print(f"Start onboarding error (failsafe): {e}")
        welcome_message = "Hey!  I'm excited to help you on your fitness journey! Let's start with a few questions to personalize your experience. What's your gender, and when were you born?"

    return {
        'message': welcome_message,
        'is_complete': False,
        'collected_data': {},
        'conversation_history': [{"role": "assistant", "content": welcome_message}],
        'next_field': 'gender',
        'recommended_macros': None,
    }
