"""Automated test script for onboarding flow."""
from onboarding import start_onboarding, onboarding, format_output_for_db
import json

# Test inputs to simulate a user
TEST_INPUTS = [
    "male",
    "19th june 2000",
    "5.9 feet",
    "80 kg",
    "70 kg",
    "lose weight",
    "fast",
    "very active",
    "yes",  # confirm macros
    "gluten free",  # dietary preference
]

def main():
    print("="*60)
    print("AUTOMATED ONBOARDING TEST")
    print("="*60)
    
    result = start_onboarding()
    print(f"\nBot: {result['message']}\n")
    
    for i, user_input in enumerate(TEST_INPUTS):
        if result['is_complete']:
            break
            
        print(f">>> User: {user_input}")
        
        result = onboarding(
            user_message=user_input,
            conversation_history=result['conversation_history'],
            collected_data=result['collected_data']
        )
        
        print(f"Bot: {result['message']}\n")
        
        if result['is_complete']:
            print("="*60)
            print("ONBOARDING COMPLETE!")
            print("="*60)
            db_output = result.get('db_format') or format_output_for_db(result['collected_data'])
            print("\nDB-Ready JSON:\n")
            print(json.dumps(db_output, indent=2))
            break
    else:
        print("\n Ran out of test inputs before completion")
        print(f"Collected: {list(result['collected_data'].keys())}")

if __name__ == "__main__":
    main()
