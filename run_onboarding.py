"""Interactive onboarding runner."""
from onboarding import start_onboarding, onboarding, format_output_for_db, ONBOARDING_FIELDS
import json

def main():
    print("="*60)
    print("FITNESS ONBOARDING - AI-Powered Data Extraction")
    print("="*60)
    print()
    
    result = start_onboarding()
    print(f"Bot: {result['message']}\n")
    
    while not result['is_complete']:
        # Count only ONBOARDING_FIELDS for progress
        collected_count = sum(1 for f in ONBOARDING_FIELDS if f in result['collected_data'])
        total_required = len(ONBOARDING_FIELDS)
        
        print(f"\n{'─'*60}")
        print(f"Progress: {collected_count}/{total_required} fields | Next: {result.get('next_field', 'dietary preferences')}")
        
        if collected_count > 0:
            fields = [f for f in result['collected_data'].keys() if f in ONBOARDING_FIELDS]
            print(f"Collected: {', '.join(fields)}")
        print(f"{'─'*60}\n")
        
        try:
            user_input = input("You: ").strip()
        except KeyboardInterrupt:
            print("\n\nOnboarding cancelled.")
            return
        
        if not user_input:
            print("Please provide an answer.\n")
            continue
        
        result = onboarding(
            user_message=user_input,
            conversation_history=result['conversation_history'],
            collected_data=result['collected_data']
        )
        
        print(f"\nBot: {result['message']}\n")
        
        if result['is_complete']:
            print("\n" + "="*60)
            print("ONBOARDING COMPLETE!")
            print("="*60)
            
            # Use the DB format output
            db_output = result.get('db_format') or format_output_for_db(result['collected_data'])
            print("\nDB-Ready JSON Output:\n")
            print(json.dumps(db_output, indent=2))
            print("\n" + "="*60)
            break

if __name__ == "__main__":
    main()