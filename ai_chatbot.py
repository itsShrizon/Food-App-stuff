"""
AI Chatbot Module - Backward Compatible Facade.

This module re-exports from the chatbot package for backward compatibility.
Actual implementation is in chatbot/service.py.
"""

from chatbot.service import ai_chatbot, _format_user_info

__all__ = ['ai_chatbot']

if __name__ == "__main__":
    from typing import Dict, List
    
    demo_user = {
        "gender": "male",
        "date_of_birth": "1990-01-01",
        "current_height": 180,
        "current_height_unit": "cm",
        "current_weight": 80,
        "current_weight_unit": "kg",
        "target_weight": 75,
        "target_weight_unit": "kg",
        "goal": "lose_weight",
        "activity_level": "moderate",
    }

    chat_history: List[Dict[str, str]] = []
    chat_history.append({"role": "assistant", "content": "Hi! How can I help?"})

    reply = ai_chatbot(
        "Suggest a quick healthy dinner from pantry items.",
        demo_user,
        conversation_history=chat_history,
    )
    print(reply["response"])
