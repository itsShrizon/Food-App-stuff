"""CLI entry to chat with the AI chatbot using the shared LLM wrapper."""

import json
from typing import Dict, List

from ai_chatbot import ai_chatbot

USER_INFO: Dict[str, str] = {
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


def main() -> None:
    conversation: List[Dict[str, str]] = []
    print("Type 'exit' to quit.\n")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break

        result = ai_chatbot(
            user_message=user_input,
            user_info=USER_INFO,
            conversation_history=conversation,
            streaming=True,
        )
        conversation = result["history"]
        print(f"AI: {result['response']}")

    print("\nConversation history:")
    print(json.dumps(conversation, indent=2))


if __name__ == "__main__":
    main()
