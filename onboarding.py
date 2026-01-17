"""Onboarding module for conversational user profile collection with macro recommendations."""

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from LLM_shared import chatbot


# Core required fields for onboarding (matching DB structure)
ONBOARDING_FIELDS = (
    'gender', 'date_of_birth',
    'current_height', 'current_height_unit',
    'current_weight', 'current_weight_unit',
    'target_weight', 'target_weight_unit',
    'goal', 
    'target_speed',
    'activity_level',
)

# Dietary preference flags (nested object in DB)
DIETARY_PREFERENCE_FLAGS = (
    'vegan', 'dairy_free', 'gluten_free', 'nut_free', 'pescatarian'
)

# Activity level multipliers for TDEE calculation
ACTIVITY_MULTIPLIERS = {
    'sedentary': 1.2,
    'light': 1.375,
    'moderate': 1.55,
    'active': 1.725,
}

# Target speed multipliers for weekly weight change
TARGET_SPEED_RATES = {
    'slow': 0.25,    # 0.25 kg per week
    'normal': 0.5,   # 0.5 kg per week
    'fast': 0.75,    # 0.75 kg per week
}

EXTRACTION_SYSTEM_PROMPT = """You are a data extraction AI. Extract fitness onboarding information from the conversation.

Required fields to extract (use EXACT field names):
- gender: "male", "female", or "others"
- date_of_birth: YYYY-MM-DD format (convert natural dates like "20 july 2000" to "2000-07-20")
- current_height: NUMERIC VALUE ONLY (e.g., 175, 69)
- current_height_unit: "cm" or "in"
- current_weight: NUMERIC VALUE ONLY (e.g., 75, 165)
- current_weight_unit: "kg" or "lb"
- target_weight: NUMERIC VALUE ONLY
- target_weight_unit: "kg" or "lb"
- goal: "lose_weight", "gain_weight", or "maintain"
- target_speed: "slow", "normal", or "fast" (default to "normal" if not mentioned)
- activity_level: "sedentary", "light", "moderate", or "active"

Dietary preferences (boolean flags):
- vegan: true/false
- dairy_free: true/false
- gluten_free: true/false
- nut_free: true/false
- pescatarian: true/false

- macros_confirmed: true if user confirmed the recommended macros

IMPORTANT RULES:
1. Extract ALL information mentioned in the conversation
2. Convert dates to YYYY-MM-DD format
3. For heights in feet/inches: convert to inches (e.g., "5 foot 9 inch" = 69, unit: "in")
4. For heights in cm: just the number (e.g., "175 cm" = 175, unit: "cm")
5. Keep weight and height as NUMERIC values, units in separate fields
6. If user says "yes", "ok", "sounds good" to macros, set macros_confirmed: true
7. Return ONLY valid JSON, no explanations

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
1. First collect: gender, age/date_of_birth, height (with unit), weight (with unit), target weight, activity level, goal
2. After all basic info → Show recommended macros and ask if they're happy with them
3. After macro confirmation → Ask about dietary preferences (vegan, dairy-free, gluten-free, nut-free, pescatarian)
4. When all done → Thank them and confirm profile is complete

RULES:
1. Be conversational and friendly - DON'T sound like a form
2. Ask one or two questions at a time
3. When asking about height/weight, clarify the unit (cm/inches, kg/lbs)
4. When showing macros, present them clearly and ask for confirmation
5. For dietary preferences, you can ask about multiple at once
6. Keep responses brief and engaging

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
    
    # Try to find JSON-like content with regex
    try:
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception:
        pass
    
    return {}


def _validate_extracted_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and sanitize extracted data to prevent hallucination issues.
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
            datetime.strptime(dob, "%Y-%m-%d")
            validated['date_of_birth'] = dob
        except ValueError:
            pass
    
    # Validate activity_level
    if 'activity_level' in data:
        level = str(data['activity_level']).lower().strip()
        if level in ACTIVITY_MULTIPLIERS:
            validated['activity_level'] = level
    
    # Validate goal (normalize to DB format)
    if 'goal' in data:
        goal = str(data['goal']).lower().strip().replace(' ', '_')
        valid_goals = ('lose_weight', 'maintain', 'gain_weight', 'lose', 'gain', 'bulk', 'cut')
        if goal in valid_goals:
            if goal in ('lose', 'cut'):
                goal = 'lose_weight'
            elif goal in ('gain', 'bulk'):
                goal = 'gain_weight'
            validated['goal'] = goal
    
    # Validate target_speed
    if 'target_speed' in data:
        speed = str(data['target_speed']).lower().strip()
        if speed in TARGET_SPEED_RATES:
            validated['target_speed'] = speed
    
    # Validate numeric fields (heights, weights) - extract numbers only
    numeric_fields = ['current_height', 'current_weight', 'target_weight']
    for field in numeric_fields:
        if field in data:
            value = data[field]
            try:
                if isinstance(value, (int, float)):
                    validated[field] = float(value)
                else:
                    # Extract numeric value from string
                    num_match = re.search(r'[\d.]+', str(value))
                    if num_match:
                        validated[field] = float(num_match.group())
            except (ValueError, TypeError):
                pass
    
    # Validate unit fields
    if 'current_height_unit' in data:
        unit = str(data['current_height_unit']).lower().strip()
        if unit in ('cm', 'in', 'inch', 'inches'):
            validated['current_height_unit'] = 'cm' if unit == 'cm' else 'in'
    
    if 'current_weight_unit' in data:
        unit = str(data['current_weight_unit']).lower().strip()
        if unit in ('kg', 'lb', 'lbs', 'pound', 'pounds'):
            validated['current_weight_unit'] = 'kg' if unit == 'kg' else 'lb'
    
    if 'target_weight_unit' in data:
        unit = str(data['target_weight_unit']).lower().strip()
        if unit in ('kg', 'lb', 'lbs', 'pound', 'pounds'):
            validated['target_weight_unit'] = 'kg' if unit == 'kg' else 'lb'
    
    # Validate dietary preference flags
    for pref in DIETARY_PREFERENCE_FLAGS:
        if pref in data:
            val = data[pref]
            if isinstance(val, bool):
                validated[pref] = val
            elif isinstance(val, str):
                validated[pref] = val.lower() in ('true', 'yes', '1')
    
    # Validate macros_confirmed
    if 'macros_confirmed' in data:
        val = data['macros_confirmed']
        if isinstance(val, bool):
            validated['macros_confirmed'] = val
        elif isinstance(val, str):
            validated['macros_confirmed'] = val.lower() in ('true', 'yes', 'ok', 'confirmed')
    
    return validated


def _convert_weight_to_kg(weight: float, unit: str) -> float:
    """Convert weight to kg based on unit."""
    if unit == 'lb':
        return weight * 0.453592
    return weight


def _convert_height_to_cm(height: float, unit: str) -> float:
    """Convert height to cm based on unit."""
    if unit == 'in':
        return height * 2.54
    return height


def calculate_metabolic_profile(
    gender: str,
    weight: float,
    weight_unit: str,
    height: float,
    height_unit: str,
    age: int,
    activity_level: str,
    goal: str,
    target_weight: float,
    target_weight_unit: str,
    target_speed: str = 'normal',
) -> Dict[str, Any]:
    """
    Calculate metabolic profile matching DB structure.
    
    Returns:
        Dictionary with: daily_calorie_target, protein_g, carbs_g, fats_g,
                        tdee, bmr, estimated_weeks_to_goal
    """
    # Convert to standard units
    weight_kg = _convert_weight_to_kg(weight, weight_unit)
    height_cm = _convert_height_to_cm(height, height_unit)
    target_weight_kg = _convert_weight_to_kg(target_weight, target_weight_unit)
    
    # Failsafe: validate ranges
    weight_kg = max(30, min(300, weight_kg)) if weight_kg > 0 else 70
    height_cm = max(100, min(250, height_cm)) if height_cm > 0 else 170
    age = max(10, min(100, age)) if age > 0 else 25
    
    # Calculate BMR using Mifflin-St Jeor equation
    if gender == 'male':
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    
    # Calculate TDEE
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.375)
    tdee = bmr * multiplier
    
    # Adjust for goal
    if goal == 'lose_weight':
        daily_calorie_target = tdee - 400
    elif goal == 'gain_weight':
        daily_calorie_target = tdee + 350
    else:
        daily_calorie_target = tdee
    
    # Ensure minimum calories
    daily_calorie_target = max(daily_calorie_target, 1200)
    
    # Calculate macros
    protein_g = round(weight_kg * 1.8, 1)
    fats_g = round(daily_calorie_target * 0.25 / 9, 1)
    carbs_g = round((daily_calorie_target - (protein_g * 4 + fats_g * 9)) / 4, 1)
    carbs_g = max(carbs_g, 50)
    
    # Calculate estimated weeks to goal
    weight_diff = abs(weight_kg - target_weight_kg)
    weekly_rate = TARGET_SPEED_RATES.get(target_speed, 0.5)
    
    if goal == 'maintain' or weight_diff < 0.5:
        estimated_weeks_to_goal = 0.0
    else:
        estimated_weeks_to_goal = round(weight_diff / weekly_rate, 1)
    
    return {
        'daily_calorie_target': round(daily_calorie_target, 1),
        'protein_g': protein_g,
        'carbs_g': carbs_g,
        'fats_g': fats_g,
        'tdee': round(tdee, 1),
        'bmr': round(bmr, 1),
        'estimated_weeks_to_goal': estimated_weeks_to_goal,
    }


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
    """
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
            temperature=0.0,
        )
        
        extracted_data = _safe_parse_json(response)
        validated_data = _validate_extracted_data(extracted_data)
        
        return validated_data
        
    except Exception as e:
        print(f"Extraction error (failsafe activated): {e}")
        return {}


def _get_default_dietary_preferences() -> Dict[str, bool]:
    """Return default dietary preferences (all False)."""
    return {pref: False for pref in DIETARY_PREFERENCE_FLAGS}


def _build_dietary_preferences(collected_data: Dict[str, Any]) -> Dict[str, bool]:
    """Build dietary preferences object from collected data."""
    prefs = _get_default_dietary_preferences()
    for pref in DIETARY_PREFERENCE_FLAGS:
        if pref in collected_data:
            prefs[pref] = bool(collected_data[pref])
    return prefs


def format_output_for_db(collected_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format collected data to match the DB structure.
    
    Returns:
        Dictionary with 'onboarding' and 'metabolic_profile' keys.
    """
    onboarding = {
        'gender': collected_data.get('gender', ''),
        'date_of_birth': collected_data.get('date_of_birth', ''),
        'current_height': collected_data.get('current_height', 0),
        'current_height_unit': collected_data.get('current_height_unit', 'cm'),
        'current_weight': collected_data.get('current_weight', 0),
        'current_weight_unit': collected_data.get('current_weight_unit', 'kg'),
        'target_weight': collected_data.get('target_weight', 0),
        'target_weight_unit': collected_data.get('target_weight_unit', 'kg'),
        'goal': collected_data.get('goal', 'maintain'),
        'target_speed': collected_data.get('target_speed', 'normal'),
        'activity_level': collected_data.get('activity_level', 'moderate'),
        'dietary_preferences': _build_dietary_preferences(collected_data),
    }
    
    metabolic_profile = collected_data.get('metabolic_profile', {
        'daily_calorie_target': 0.0,
        'protein_g': 0.0,
        'carbs_g': 0.0,
        'fats_g': 0.0,
        'tdee': 0.0,
        'bmr': 0.0,
        'estimated_weeks_to_goal': 0.0,
    })
    
    return {
        'onboarding': onboarding,
        'metabolic_profile': metabolic_profile,
    }


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
    
    Returns:
        Dictionary containing:
            - message: Bot's response/next question
            - conversation_history: Updated conversation history
            - collected_data: Updated collected profile data
            - is_complete: Boolean indicating if onboarding is complete
            - next_field: Next field to collect (if not complete)
            - metabolic_profile: Calculated metabolic profile (if available)
            - db_format: Data formatted for DB insertion (when complete)
    """
    conversation_history = list(conversation_history or [])
    collected_data = dict(collected_data or {})
    
    conversation_history.append({"role": "user", "content": user_message})
    
    # Extract data with failsafe
    try:
        extracted_data = _extract_data_with_llm(conversation_history, model=model)
    except Exception:
        extracted_data = {}
    
    # Update collected data
    all_fields = ONBOARDING_FIELDS + DIETARY_PREFERENCE_FLAGS + ('macros_confirmed',)
    for field, value in extracted_data.items():
        if field in all_fields and value is not None:
            collected_data[field] = value
    
    # Check if we have all required fields for metabolic calculation
    required_for_macros = [
        'gender', 'date_of_birth', 
        'current_height', 'current_height_unit',
        'current_weight', 'current_weight_unit',
        'target_weight', 'target_weight_unit',
        'activity_level', 'goal'
    ]
    have_all_for_macros = all(f in collected_data for f in required_for_macros)
    
    macros_calculated = 'metabolic_profile' in collected_data
    macros_confirmed = collected_data.get('macros_confirmed', False)
    
    # Calculate metabolic profile if we have all required fields
    if have_all_for_macros and not macros_calculated:
        try:
            metabolic = calculate_metabolic_profile(
                gender=collected_data['gender'],
                weight=collected_data['current_weight'],
                weight_unit=collected_data['current_weight_unit'],
                height=collected_data['current_height'],
                height_unit=collected_data['current_height_unit'],
                age=_calculate_age(collected_data['date_of_birth']),
                activity_level=collected_data['activity_level'],
                goal=collected_data['goal'],
                target_weight=collected_data['target_weight'],
                target_weight_unit=collected_data['target_weight_unit'],
                target_speed=collected_data.get('target_speed', 'normal'),
            )
            collected_data['metabolic_profile'] = metabolic
            macros_calculated = True
        except Exception as e:
            print(f"Metabolic calculation error (failsafe): {e}")
    
    # Determine missing required fields
    missing_fields = [f for f in ONBOARDING_FIELDS if f not in collected_data]
    
    # Default target_speed to normal if not provided
    if 'target_speed' not in collected_data and not missing_fields:
        collected_data['target_speed'] = 'normal'
    
    # Check for dietary preferences after macros confirmed
    dietary_complete = any(pref in collected_data for pref in DIETARY_PREFERENCE_FLAGS)
    
    # Check if onboarding is complete
    is_complete = (
        len(missing_fields) == 0 and 
        macros_confirmed and
        (dietary_complete or collected_data.get('dietary_skipped', False))
    )
    
    # Handle skip keywords
    skip_keywords = ['skip', 'none', 'no ', 'nothing', "don't have", "dont have", "no restrictions", "no allergies", "no preferences"]
    if any(kw in user_message.lower() for kw in skip_keywords):
        if not missing_fields and macros_confirmed:
            collected_data['dietary_skipped'] = True
            is_complete = True
    
    if is_complete:
        final_message = "Thank you! I have all the information I need. Your profile is complete!\n\n"
        
        if 'metabolic_profile' in collected_data:
            mp = collected_data['metabolic_profile']
            final_message += f"**Your Daily Targets:**\n"
            final_message += f"- Calories: {mp['daily_calorie_target']} kcal\n"
            final_message += f"- Protein: {mp['protein_g']}g\n"
            final_message += f"- Carbs: {mp['carbs_g']}g\n"
            final_message += f"- Fat: {mp['fats_g']}g\n"
            if mp['estimated_weeks_to_goal'] > 0:
                final_message += f"\nEstimated time to reach your goal: {mp['estimated_weeks_to_goal']} weeks"
        
        conversation_history.append({"role": "assistant", "content": final_message})
        
        return {
            "message": final_message,
            "conversation_history": conversation_history,
            "collected_data": collected_data,
            "is_complete": True,
            "next_field": None,
            "metabolic_profile": collected_data.get('metabolic_profile'),
            "db_format": format_output_for_db(collected_data),
        }
    
    # Build context for conversation
    collected_fields_str = ", ".join(collected_data.keys()) if collected_data else "none"
    missing_fields_str = ", ".join(missing_fields) if missing_fields else "none"
    
    # Build macro info for system prompt
    macro_info = ""
    if macros_calculated and not macros_confirmed:
        mp = collected_data['metabolic_profile']
        macro_info = f"""
IMPORTANT: Show the user their recommended daily targets and ask if they're happy with them:
- Calories: {mp['daily_calorie_target']} kcal/day
- Protein: {mp['protein_g']}g
- Carbs: {mp['carbs_g']}g  
- Fat: {mp['fats_g']}g
- Estimated weeks to goal: {mp['estimated_weeks_to_goal']}

Ask: "Are you happy with these recommendations, or would you like to adjust them?"
"""
    elif macros_confirmed and not dietary_complete:
        macro_info = "Macros confirmed! Now ask about dietary preferences (vegan, dairy-free, gluten-free, nut-free, pescatarian). They can say 'none' if no restrictions."
    
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
            conversation_history=conversation_history[:-1],
            model=model,
            temperature=temperature,
            **kwargs,
        )
    except Exception as e:
        print(f"Chatbot error (failsafe): {e}")
        if missing_fields:
            bot_response = f"I'd love to hear more! Could you tell me about your {missing_fields[0].replace('_', ' ')}?"
        elif macros_calculated and not macros_confirmed:
            mp = collected_data['metabolic_profile']
            bot_response = f"Based on your profile, I recommend {mp['daily_calorie_target']} calories daily. Does that sound good?"
        else:
            bot_response = "Do you have any dietary preferences or restrictions I should know about? (vegan, dairy-free, gluten-free, nut-free, pescatarian)"
    
    conversation_history.append({"role": "assistant", "content": bot_response})
    
    return {
        "message": bot_response,
        "conversation_history": conversation_history,
        "collected_data": collected_data,
        "is_complete": False,
        "next_field": missing_fields[0] if missing_fields else None,
        "metabolic_profile": collected_data.get('metabolic_profile'),
        "db_format": None,
    }


def start_onboarding(
    *,
    model: str = "gpt-4.1-nano",
    temperature: float = 0.7,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Start a new onboarding conversation.

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
        print(f"Start onboarding error (failsafe): {e}")
        welcome_message = "Hey! I'm excited to help you on your fitness journey! Let's start with a few questions to personalize your experience. What's your gender, and when were you born?"

    return {
        'message': welcome_message,
        'is_complete': False,
        'collected_data': {},
        'conversation_history': [{"role": "assistant", "content": welcome_message}],
        'next_field': 'gender',
        'metabolic_profile': None,
        'db_format': None,
    }


# Legacy compatibility aliases
def calculate_macros(
    gender: str,
    weight_kg: float,
    height_cm: float,
    age: int,
    activity_level: str,
    goal: str,
) -> Dict[str, Any]:
    """Legacy function for backward compatibility."""
    return calculate_metabolic_profile(
        gender=gender,
        weight=weight_kg,
        weight_unit='kg',
        height=height_cm,
        height_unit='cm',
        age=age,
        activity_level=activity_level,
        goal=goal,
        target_weight=weight_kg,
        target_weight_unit='kg',
        target_speed='normal',
    )
