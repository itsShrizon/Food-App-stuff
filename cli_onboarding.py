"""Interactive CLI for the Onboarding Service."""
import json
import sys
import os

# Ensure the app module is in the path
sys.path.append(os.getcwd())

from app.services.onboarding.start import start_onboarding
from app.services.onboarding.flow import onboarding
from app.services.onboarding.config import ONBOARDING_FIELDS
from app.services.onboarding.formatter import format_output_for_db

def main():
    print("="*60)
    print("FITNESS ONBOARDING CLI - AI-Powered Data Extraction")
    print("="*60)
    print("This CLI tests the standalone onboarding logic in 'app/services/onboarding'.")
    print()
    
    # 1. Start the session
    result = start_onboarding()
    print(f"Bot: {result['message']}\n")
    
    # 2. Loop until complete
    while not result['is_complete']:
        # Calculate progress
        collected_count = sum(1 for f in ONBOARDING_FIELDS if f in result['collected_data'])
        total_required = len(ONBOARDING_FIELDS)
        
        # Display Status
        print(f"\n{'─'*60}")
        print(f"Progress: {collected_count}/{total_required} fields | Next: {result.get('next_field', 'dietary preferences')}")
        
        if collected_count > 0:
            fields = [f for f in result['collected_data'].keys() if f in ONBOARDING_FIELDS]
            # Wrap long lists
            fields_str = ', '.join(fields)
            if len(fields_str) > 80:
                fields_str = fields_str[:77] + "..."
            print(f"Collected: {fields_str}")
        print(f"{'─'*60}\n")
        
        # Get Input
        try:
            user_input = input("You: ").strip()
        except KeyboardInterrupt:
            print("\n\nOnboarding cancelled.")
            return
        
        if not user_input:
            print("Please provide an answer.\n")
            continue
        
        if user_input.lower() in ['exit', 'quit']:
             print("\nExiting onboarding.")
             return

        # 3. Process Input
        result = onboarding(
            user_message=user_input,
            conversation_history=result['conversation_history'],
            collected_data=result['collected_data']
        )
        
        print(f"\nBot: {result['message']}\n")
        
        # 4. Handle Completion
        if result['is_complete']:
            print("\n" + "="*60)
            print("ONBOARDING COMPLETE!")
            print("="*60)
            
            # Format and show DB-ready output
            db_output = result.get('db_format') or format_output_for_db(result['collected_data'])
            print("\nDB-Ready JSON Output:\n")
            print(json.dumps(db_output, indent=2))
            print("\n" + "="*60)
            break

if __name__ == "__main__":
    main()
