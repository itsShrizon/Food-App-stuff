from onboarding import start_onboarding, onboarding
import json

def main():
    print("="*60)
    print("🏋️  FITNESS ONBOARDING - LLM-Powered Data Extraction")
    print("="*60)
    print()
    
    # Start onboarding
    result = start_onboarding()
    print(f"Bot: {result['message']}\n")
    
    # Continue conversation until complete
    while not result['is_complete']:
        # Show progress
        collected_count = len(result['collected_data'])
        total_required = 14
        print(f"\n{'─'*60}")
        print(f"📊 Progress: {collected_count}/{total_required} fields | Next: {result.get('next_field', 'N/A')}")
        
        if collected_count > 0:
            print(f"✓ Collected: {', '.join(result['collected_data'].keys())}")
        print(f"{'─'*60}\n")
        
        # Get user input
        try:
            user_input = input("You: ").strip()
        except KeyboardInterrupt:
            print("\n\n👋 Onboarding cancelled. Goodbye!")
            return
        
        if not user_input:
            print("Please provide an answer.\n")
            continue
        
        # Process response with LLM extraction
        print("\n🤖 Processing with AI...", end="", flush=True)
        result = onboarding(
            user_message=user_input,
            conversation_history=result['conversation_history'],
            collected_data=result['collected_data']
        )
        print("\r" + " "*30 + "\r", end="")  # Clear processing message
        
        print(f"Bot: {result['message']}\n")
        
        if result['is_complete']:
            print("\n" + "="*60)
            print("✅ ONBOARDING COMPLETE!")
            print("="*60)
            print("\n📋 Collected Profile Data (JSON):\n")
            print(json.dumps(result['collected_data'], indent=2))
            print("\n" + "="*60)
            print("✨ This data is ready to send to your backend!")
            print("="*60)
            break

if __name__ == "__main__":
    main()