"""Automated test script for onboarding flow."""
from onboarding import start_onboarding, onboarding, format_output_for_db
import json

# Test inputs - must follow the correct order
TEST_INPUTS = [
    "male",                    # gender
    "19th june 2000",          # date_of_birth  
    "175 cm",                  # height with unit
    "80 kg",                   # current weight with unit
    "70 kg",                   # target weight with unit
    "lose weight",             # goal
    "normal",                  # target speed
    "active",                  # activity level
    "yes",                     # confirm macros
    "gluten free",             # dietary preference
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
            
        print(f">>> [{i+1}] User: {user_input}")
        
        result = onboarding(
            user_message=user_input,
            conversation_history=result['conversation_history'],
            collected_data=result['collected_data']
        )
        
        print(f"Bot: {result['message'][:200]}...")
        print(f"    Collected: {list(result['collected_data'].keys())}")
        print()
        
        if result['is_complete']:
            print("="*60)
            print("ONBOARDING COMPLETE!")
            print("="*60)
            db_output = result.get('db_format') or format_output_for_db(result['collected_data'])
            print("\nDB-Ready JSON:\n")
            print(json.dumps(db_output, indent=2))
            break
    else:
        print("\n⚠️ Ran out of test inputs before completion")
        print(f"Missing: {[f for f in ['gender', 'date_of_birth', 'current_height', 'current_height_unit', 'current_weight', 'current_weight_unit', 'target_weight', 'target_weight_unit', 'goal', 'target_speed', 'activity_level'] if f not in result['collected_data']]}")

if __name__ == "__main__":
    main()
