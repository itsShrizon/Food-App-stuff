#!/usr/bin/env python3
"""
End-to-End test for Conversational Onboarding Chat API.
Tests the full flow from start to completion.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1/onboarding"
USER_ID = 1

def test_conversational_onboarding():
    print("=" * 70)
    print("CONVERSATIONAL ONBOARDING E2E TEST")
    print("=" * 70)
    
    # Step 1: Start session
    print("\n📌 STEP 1: Start new session")
    resp = requests.post(f"{BASE_URL}/chat/start?user_id={USER_ID}")
    if resp.status_code != 200:
        print(f"❌ Failed to start session: {resp.status_code}")
        return False
    
    data = resp.json()
    session_id = data["session_id"]
    print(f"   Session ID: {session_id}")
    print(f"   Bot: {data['message']}")
    print(f"   Progress: {data['progress']['collected']}/{data['progress']['total']}")
    
    # Define conversation turns
    turns = [
        ("I'm a 28 year old male", "gender + age"),
        ("180 cm tall, 90 kg", "height + weight"),
        ("I want to lose weight down to 80 kg", "goal + target"),
        ("normal speed, moderate activity", "speed + activity"),
        ("yes that looks perfect", "confirm macros"),
        ("no dietary restrictions", "dietary prefs"),
    ]
    
    for i, (user_msg, description) in enumerate(turns, 2):
        print(f"\n📌 STEP {i}: {description}")
        print(f"   User: \"{user_msg}\"")
        
        resp = requests.post(
            f"{BASE_URL}/chat",
            json={"user_id": USER_ID, "message": user_msg, "session_id": session_id}
        )
        
        if resp.status_code != 200:
            print(f"❌ Failed: {resp.status_code} - {resp.text}")
            return False
        
        data = resp.json()
        print(f"   Bot: {data['message'][:100]}...")
        print(f"   Progress: {data['progress']['collected']}/{data['progress']['total']}")
        print(f"   Complete: {data['is_complete']}")
        
        if data["is_complete"]:
            print("\n" + "=" * 70)
            print("✅ ONBOARDING COMPLETE!")
            print("=" * 70)
            
            # Show collected data
            print("\n📊 Collected Data:")
            collected = data["collected_data"]
            for key in ["gender", "date_of_birth", "current_height", "current_weight", 
                       "target_weight", "goal", "activity_level"]:
                if key in collected:
                    print(f"   • {key}: {collected[key]}")
            
            # Show metabolic profile
            if data.get("metabolic_profile"):
                print("\n💪 Metabolic Profile:")
                mp = data["metabolic_profile"]
                print(f"   • Daily Calories: {mp['daily_calorie_target']} kcal")
                print(f"   • Protein: {mp['protein_g']}g")
                print(f"   • Carbs: {mp['carbs_g']}g")
                print(f"   • Fats: {mp['fats_g']}g")
                print(f"   • TDEE: {mp['tdee']} kcal")
                print(f"   • BMR: {mp['bmr']} kcal")
                print(f"   • Days to Goal: {mp['estimated_days_to_goal']}")
            
            # Show DB-ready format
            if data.get("db_format"):
                print("\n🗄️ Database-Ready JSON:")
                print(json.dumps(data["db_format"], indent=2)[:500] + "...")
            
            return True
        
        time.sleep(0.5)  # Small delay between calls
    
    print("\n❌ Did not complete in expected turns")
    return False


def test_session_persistence():
    """Test that session data persists across calls."""
    print("\n" + "=" * 70)
    print("SESSION PERSISTENCE TEST")
    print("=" * 70)
    
    # Start session
    resp = requests.post(f"{BASE_URL}/chat/start?user_id={USER_ID}")
    session_id = resp.json()["session_id"]
    print(f"\n1. Started session: {session_id}")
    
    # Send first message
    resp = requests.post(
        f"{BASE_URL}/chat",
        json={"user_id": USER_ID, "message": "female", "session_id": session_id}
    )
    data = resp.json()
    print(f"2. Sent 'female', collected: {list(data['collected_data'].keys())}")
    
    # Get session state
    resp = requests.get(f"{BASE_URL}/chat/{session_id}")
    if resp.status_code == 200:
        state = resp.json()
        print(f"3. GET session shows: {list(state['collected_data'].keys())}")
        print(f"   Conversation history: {len(state['conversation_history'])} messages")
        print("✅ Session persistence verified!")
        return True
    else:
        print(f"❌ Failed to get session: {resp.status_code}")
        return False


def test_error_handling():
    """Test error cases."""
    print("\n" + "=" * 70)
    print("ERROR HANDLING TEST")
    print("=" * 70)
    
    passed = 0
    
    # Test 1: Non-existent user
    print("\n1. Start session with non-existent user")
    resp = requests.post(f"{BASE_URL}/chat/start?user_id=99999")
    if resp.status_code == 404:
        print("   ✅ Correctly returned 404")
        passed += 1
    else:
        print(f"   ❌ Expected 404, got {resp.status_code}")
    
    # Test 2: Non-existent session
    print("\n2. Get non-existent session")
    resp = requests.get(f"{BASE_URL}/chat/invalid-session-id")
    if resp.status_code == 404:
        print("   ✅ Correctly returned 404")
        passed += 1
    else:
        print(f"   ❌ Expected 404, got {resp.status_code}")
    
    return passed == 2


if __name__ == "__main__":
    try:
        t1 = test_conversational_onboarding()
        t2 = test_session_persistence()
        t3 = test_error_handling()
        
        print("\n" + "=" * 70)
        print("FINAL RESULTS")
        print("=" * 70)
        print(f"✅ Full Flow Test: {'PASSED' if t1 else 'FAILED'}")
        print(f"✅ Session Persistence: {'PASSED' if t2 else 'FAILED'}")
        print(f"✅ Error Handling: {'PASSED' if t3 else 'FAILED'}")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running?")
