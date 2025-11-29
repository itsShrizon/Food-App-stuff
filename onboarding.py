"""Onboarding module for conversational user profile collection."""

import json
from typing import Any, Dict, List, Optional

from LLM_shared import chatbot


ONBOARDING_FIELDS = (
    'gender', 'date_of_birth',
    'current_height', 
    'current_weight', 
    'target_weight', 
    'goal', 
    'target_speed', 
    'activity_level'
)

EXTRACTION_SYSTEM_PROMPT = """You are a data extraction AI. Extract fitness onboarding information from the conversation.

Required fields to extract:
- gender: male, female, or others
- date_of_birth: YYYY-MM-DD format
- current_height: numeric value and unit
- current_weight: numeric value and unit
- target_weight: numeric value and unit
- goal: "lose weight", "maintain", or "gain weight" 
- target_speed: "slow", "normal", or "fast"
- activity_level: "sedentary", "light", "moderate", or "active"

IMPORTANT RULES:
1. Extract ALL information mentioned in the conversation
2. Convert dates to YYYY-MM-DD format (e.g., "20 july 2000" → "2000-07-20")
3. Convert heights: feet/inches to inches (e.g., "5 foot 9 inch" → 69 inches, unit: "inch")
4. If target height/weight not mentioned, ask for it later
5. If target_speed not mentioned, default to "normal"
6. Only return fields that have been mentioned or can be inferred
7. Return ONLY valid JSON, no explanations

Return format:
{
  "field_name": "extracted_value"
}"""

CONVERSATION_SYSTEM_PROMPT = """You are a friendly fitness onboarding assistant. Have a natural conversation to collect user information.

Required information to collect:
✓ Gender (male/female/others)
✓ Date of birth
✓ Current height and unit (cm/inches)
✓ Target height and unit (if different from current)
✓ Current weight and unit (kg/lbs)
✓ Target weight and unit (if different from current)
✓ Fitness goal (lose weight/maintain/gain weight)
✓ Preferred pace (slow/normal/fast)
✓ Current activity level (sedentary/light/moderate/active)

RULES:
1. Be conversational and natural - DON'T sound like a form
2. Ask single, clear questions to get one piece of info at a time
3. If user provides multiple pieces of info at once, acknowledge all of it
4. Keep responses brief and friendly
5. When all info is collected, say "Thank you! I have all the information I need."

Current collected fields: {collected_fields}
Missing fields: {missing_fields}

Be natural and conversational!"""


def _extract_data_with_llm(
    conversation_history: List[Dict[str, str]],
    model: str = "gpt-4.1-nano",
) -> Dict[str, Any]:
    """
    Use LLM to intelligently extract all data from conversation.
    
    Args:
        conversation_history: Full conversation history
        model: Model to use for extraction
        
    Returns:
        Dictionary of extracted field values
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
        

        response = response.strip()
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        
        extracted_data = json.loads(response.strip())
        return extracted_data
    except Exception as e:
        print(f"Extraction error: {e}")
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
    
    Args:
        user_message: User's response to the current question
        conversation_history: List of previous messages
        collected_data: Dictionary of already collected profile data
        model: OpenAI model to use (default: gpt-4o-mini for better extraction)
        temperature: Model temperature
        **kwargs: Additional parameters for chatbot
        
    Returns:
        Dictionary containing:
            - message: Bot's response/next question
            - conversation_history: Updated conversation history
            - collected_data: Updated collected profile data
            - is_complete: Boolean indicating if onboarding is complete
            - next_field: Next field to collect (if not complete)
    """
    # Initialize
    conversation_history = list(conversation_history or [])
    collected_data = dict(collected_data or {})
    
    # Add user message to history
    conversation_history.append({"role": "user", "content": user_message})
    
    # Use LLM to extract data from entire conversation
    extracted_data = _extract_data_with_llm(conversation_history, model=model)
    
    # Update collected data with newly extracted info
    for field, value in extracted_data.items():
        if field in ONBOARDING_FIELDS and value:
            collected_data[field] = value
    
    # Determine missing fields
    missing_fields = [f for f in ONBOARDING_FIELDS if f not in collected_data]
    
    # Check if onboarding is complete
    is_complete = len(missing_fields) == 0
    
    if is_complete:
        final_message = "Thank you! I have all the information I need. Your profile is complete! 🎉"
        conversation_history.append({"role": "assistant", "content": final_message})
        
        return {
            "message": final_message,
            "conversation_history": conversation_history,
            "collected_data": collected_data,
            "is_complete": True,
            "next_field": None,
        }
    
    # Generate next question based on what's missing
    collected_fields_str = ", ".join(collected_data.keys()) if collected_data else "none"
    missing_fields_str = ", ".join(missing_fields)
    
    system_prompt = CONVERSATION_SYSTEM_PROMPT.format(
        collected_fields=collected_fields_str,
        missing_fields=missing_fields_str,
    )
    
    # Get bot response
    bot_response = chatbot(
        user_message=f"User said: '{user_message}'. What should I ask next to collect: {missing_fields_str[:100]}?",
        system_prompt=system_prompt,
        conversation_history=conversation_history[:-1],  # Exclude last message
        model=model,
        temperature=temperature,
        **kwargs,
    )
    
    # Add bot response to history
    conversation_history.append({"role": "assistant", "content": bot_response})
    
    return {
        "message": bot_response,
        "conversation_history": conversation_history,
        "collected_data": collected_data,
        "is_complete": False,
        "next_field": missing_fields[0] if missing_fields else None,
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
        model: OpenAI model identifier. Defaults to "gpt-4o-mini".
        temperature: Sampling temperature. Defaults to 0.7.
        **kwargs: Additional arguments passed to chatbot function.

    Returns:
        Dict containing initial onboarding state with welcome message.
    """
    missing_fields_str = ", ".join(ONBOARDING_FIELDS)
    
    system_prompt = CONVERSATION_SYSTEM_PROMPT.format(
        collected_fields="none",
        missing_fields=missing_fields_str,
    )

    welcome_message = chatbot(
        user_message="Start the fitness onboarding. Greet warmly and ask about basic info (gender, age, height, weight) in a natural way.",
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
