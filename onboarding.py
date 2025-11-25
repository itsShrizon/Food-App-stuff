"""Onboarding module for conversational user profile collection."""

import json
from typing import Any, Dict, List, Optional

from LLM_shared import chatbot


ONBOARDING_FIELDS = (
    'gender', 'date_of_birth', 'image',
    'current_height', 'current_height_unit',
    'target_height', 'target_height_unit',
    'current_weight', 'current_weight_unit',
    'target_weight', 'target_weight_unit',
    'goal', 'target_timeline_value', 'target_timeline_unit',
    'target_speed', 'activity_level'
)

SYSTEM_PROMPT = """You are a friendly fitness onboarding assistant. Your job is to collect user information conversationally.

Follow these rules strictly:
1. Ask ONE question at a time
2. Be friendly and encouraging
3. Validate user responses
4. If user provides invalid data, politely ask again
5. Use the provided field choices for validation
6. Keep questions clear and concise

Available choices:
- Gender: male, female, others
- Height units: cm (centimeters), inch (inches)
- Weight units: kg (kilograms), lbs (pounds)
- Goals: lose_weight, maintain, gain_weight
- Timeline units: days, weeks, months, years
- Target speed: slow, normal, fast
- Activity level: sedentary, light, moderate, active

Current field to collect: {current_field}
Already collected: {collected_fields}

Ask the next question naturally."""


def onboarding(
    user_message: str,
    *,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    collected_data: Optional[Dict[str, Any]] = None,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.7,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Execute conversational onboarding to collect user profile data.

    This function manages a multi-turn conversation to collect all required
    onboarding fields. It asks questions one at a time and validates responses
    before moving to the next field.

    Args:
        user_message: The user's current response.
        conversation_history: Previous conversation messages. Defaults to None.
        collected_data: Already collected profile data. Defaults to None (empty dict).
        model: OpenAI model identifier. Defaults to "gpt-3.5-turbo".
        temperature: Sampling temperature. Defaults to 0.7.
        **kwargs: Additional arguments passed to chatbot function.

    Returns:
        Dict containing:
            - 'message': The next question or completion message
            - 'is_complete': Boolean indicating if all data is collected
            - 'collected_data': Dictionary of collected profile fields
            - 'conversation_history': Updated conversation history
            - 'next_field': The next field to collect (if not complete)

    Example:
        >>> result = onboarding("I'm male")
        >>> print(result['message'])
        "Great! What is your date of birth? (Format: YYYY-MM-DD)"
        >>> print(result['is_complete'])
        False
    """
    if collected_data is None:
        collected_data = {}
    else:
        collected_data = dict(collected_data)  # Create a copy to avoid mutating input
    
    if conversation_history is None:
        conversation_history = []
    else:
        conversation_history = list(conversation_history)  # Create a copy to avoid mutating input

    # Extract and validate data from user message FIRST
    # Determine which field we're currently collecting
    current_field = None
    for field in ONBOARDING_FIELDS:
        if field not in collected_data:
            current_field = field
            break

    # Try to extract value from user message if we have a field to collect
    if current_field:
        extracted_value = _extract_field_value(user_message, current_field, collected_data)
        if extracted_value is not None:
            collected_data[current_field] = extracted_value

    # Now determine next field to collect AFTER extraction
    next_field = None
    for field in ONBOARDING_FIELDS:
        if field not in collected_data:
            next_field = field
            break

    # Check if onboarding is complete
    if next_field is None:
        return {
            'message': 'Thank you! Your onboarding is complete.',
            'is_complete': True,
            'collected_data': collected_data,
            'conversation_history': conversation_history,
            'next_field': None,
        }

    # Build system prompt with context
    collected_fields = list(collected_data.keys())
    system_prompt = SYSTEM_PROMPT.format(
        current_field=next_field if next_field else "complete",
        collected_fields=", ".join(collected_fields) if collected_fields else "none"
    )

    # Get AI response
    ai_message = chatbot(
        user_message=user_message,
        system_prompt=system_prompt,
        conversation_history=conversation_history,
        model=model,
        temperature=temperature,
        **kwargs,
    )

    # Update conversation history
    conversation_history.append({"role": "user", "content": user_message})
    conversation_history.append({"role": "assistant", "content": ai_message})

    return {
        'message': ai_message,
        'is_complete': False,
        'collected_data': collected_data,
        'conversation_history': conversation_history,
        'next_field': next_field,
    }


def _extract_field_value(
    user_message: str,
    field_name: str,
    collected_data: Dict[str, Any],
) -> Optional[Any]:
    """
    Extract and validate field value from user message.

    Args:
        user_message: The user's response.
        field_name: The field being collected.
        collected_data: Already collected data for context.

    Returns:
        Extracted value if valid, None otherwise.
    """
    user_message_lower = user_message.lower().strip()

    # Gender extraction
    if field_name == 'gender':
        if any(word in user_message_lower for word in ['female', 'woman', 'girl']):
            return 'female'
        elif any(word in user_message_lower for word in ['male', 'man', 'boy']):
            return 'male'
        elif any(word in user_message_lower for word in ['other', 'non-binary', 'prefer not']):
            return 'others'

    # Date of birth extraction (basic validation)
    elif field_name == 'date_of_birth':
        # Look for date patterns (YYYY-MM-DD, MM/DD/YYYY, etc.)
        import re
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{2}-\d{2}-\d{4}',  # DD-MM-YYYY
        ]
        for pattern in date_patterns:
            match = re.search(pattern, user_message)
            if match:
                return match.group(0)

    # Height extraction
    elif field_name == 'current_height':
        import re
        numbers = re.findall(r'\d+\.?\d*', user_message)
        if numbers:
            return float(numbers[0])

    elif field_name == 'current_height_unit':
        if 'cm' in user_message_lower or 'centimeter' in user_message_lower:
            return 'cm'
        elif 'inch' in user_message_lower or 'in' in user_message_lower:
            return 'inch'

    elif field_name == 'target_height':
        import re
        numbers = re.findall(r'\d+\.?\d*', user_message)
        if numbers:
            return float(numbers[0])

    elif field_name == 'target_height_unit':
        if 'cm' in user_message_lower or 'centimeter' in user_message_lower:
            return 'cm'
        elif 'inch' in user_message_lower or 'in' in user_message_lower:
            return 'inch'

    # Weight extraction
    elif field_name == 'current_weight':
        import re
        numbers = re.findall(r'\d+\.?\d*', user_message)
        if numbers:
            return float(numbers[0])

    elif field_name == 'current_weight_unit':
        if 'kg' in user_message_lower or 'kilogram' in user_message_lower:
            return 'kg'
        elif 'lb' in user_message_lower or 'pound' in user_message_lower:
            return 'lbs'

    elif field_name == 'target_weight':
        import re
        numbers = re.findall(r'\d+\.?\d*', user_message)
        if numbers:
            return float(numbers[0])

    elif field_name == 'target_weight_unit':
        if 'kg' in user_message_lower or 'kilogram' in user_message_lower:
            return 'kg'
        elif 'lb' in user_message_lower or 'pound' in user_message_lower:
            return 'lbs'

    # Goal extraction
    elif field_name == 'goal':
        if any(word in user_message_lower for word in ['lose', 'loss', 'reduce']):
            return 'lose_weight'
        elif any(word in user_message_lower for word in ['maintain', 'stay', 'keep']):
            return 'maintain'
        elif any(word in user_message_lower for word in ['gain', 'build', 'increase']):
            return 'gain_weight'

    # Timeline extraction
    elif field_name == 'target_timeline_value':
        import re
        numbers = re.findall(r'\d+', user_message)
        if numbers:
            return int(numbers[0])

    elif field_name == 'target_timeline_unit':
        if 'day' in user_message_lower:
            return 'days'
        elif 'week' in user_message_lower:
            return 'weeks'
        elif 'month' in user_message_lower:
            return 'months'
        elif 'year' in user_message_lower:
            return 'years'

    # Target speed extraction
    elif field_name == 'target_speed':
        if 'slow' in user_message_lower:
            return 'slow'
        elif 'normal' in user_message_lower or 'moderate' in user_message_lower:
            return 'normal'
        elif 'fast' in user_message_lower or 'quick' in user_message_lower:
            return 'fast'

    # Activity level extraction
    elif field_name == 'activity_level':
        if 'sedentary' in user_message_lower or 'inactive' in user_message_lower:
            return 'sedentary'
        elif 'light' in user_message_lower:
            return 'light'
        elif 'moderate' in user_message_lower:
            return 'moderate'
        elif 'active' in user_message_lower or 'very active' in user_message_lower:
            return 'active'

    # Image field (skip for now, requires file upload handling)
    elif field_name == 'image':
        if 'skip' in user_message_lower or 'no' in user_message_lower or 'later' in user_message_lower:
            return 'users/avatar.png'  # Default
        return None  # Requires special handling

    return None


def start_onboarding(
    *,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.7,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Start a new onboarding conversation.

    Args:
        model: OpenAI model identifier. Defaults to "gpt-3.5-turbo".
        temperature: Sampling temperature. Defaults to 0.7.
        **kwargs: Additional arguments passed to chatbot function.

    Returns:
        Dict containing initial onboarding state with welcome message.
    """
    system_prompt = SYSTEM_PROMPT.format(
        current_field='gender',
        collected_fields='none'
    )

    welcome_message = chatbot(
        user_message="Start the onboarding process. Greet the user and ask the first question about their gender.",
        system_prompt=system_prompt,
        model=model,
        temperature=temperature,
        **kwargs,
    )

    return {
        'message': welcome_message,
        'is_complete': False,
        'collected_data': {},
        'conversation_history': [{"role": "assistant", "content": welcome_message}],
        'next_field': 'gender',
    }
