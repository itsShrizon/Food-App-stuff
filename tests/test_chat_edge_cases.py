#!/usr/bin/env python3
"""
Edge Case Tests for Conversational Onboarding Chat API.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1/onboarding"
USER_ID = 1

def chat(session_id, message):
    """Helper to send chat message."""
    resp = requests.post(
        f"{BASE_URL}/chat",
        json={"user_id": USER_ID, "message": message, "session_id": session_id}
    )
    return resp.json() if resp.status_code == 200 else None

def start_session():
    """Start a new session."""
    resp = requests.post(f"{BASE_URL}/chat/start?user_id={USER_ID}")
    return resp.json()["session_id"] if resp.status_code == 200 else None

def run_edge_case(name, messages, expected_check):
    """Run an edge case test."""
    print(f"\n{'─'*60}")
    print(f"📋 {name}")
    print(f"{'─'*60}")
    
    session_id = start_session()
    if not session_id:
        print("❌ Failed to start session")
        return False
    
    result = None
    for i, msg in enumerate(messages, 1):
        print(f"   {i}. User: \"{msg[:50]}...\"" if len(msg) > 50 else f"   {i}. User: \"{msg}\"")
        result = chat(session_id, msg)
        if not result:
            print("   ❌ API call failed")
            return False
        print(f"      → {result['progress']['collected']}/{result['progress']['total']} fields")
        time.sleep(0.3)
    
    # Run expected check
    passed, reason = expected_check(result)
    if passed:
        print(f"   ✅ PASSED: {reason}")
    else:
        print(f"   ❌ FAILED: {reason}")
    return passed

# ============================================================================
# EDGE CASE DEFINITIONS
# ============================================================================

EDGE_CASES = [
    # --- Natural Language Variations ---
    {
        "name": "Slang & Informal Language",
        "messages": [
            "yo im a dude, 25",
            "like 5 foot 10, around 180 lbs",
            "wanna drop some pounds to like 160",
            "normal i guess, pretty active",
            "yeah looks good bro",
            "nah no restrictions"
        ],
        "check": lambda r: (r.get("is_complete"), "Completed with slang")
    },
    {
        "name": "Typos & Misspellings",
        "messages": [
            "mal 30 yeers old",
            "175 centimters, 85 kilograms",
            "loose wieght to 75",
            "moderete activty",
            "yess",
            "none"
        ],
        "check": lambda r: (r.get("is_complete"), "Handled typos")
    },
    {
        "name": "ALL CAPS Input",
        "messages": [
            "MALE 25 YEARS OLD",
            "180 CM 80 KG",
            "MAINTAIN WEIGHT",
            "ACTIVE",
            "YES",
            "VEGAN"
        ],
        "check": lambda r: (r.get("is_complete"), "Processed ALL CAPS")
    },
    
    # --- Multi-Field Inputs ---
    {
        "name": "Everything in One Message",
        "messages": [
            "Male, 28, 180cm, 85kg, want to lose to 75kg, moderate activity, normal speed",
            "yes",
            "no restrictions"
        ],
        "check": lambda r: (r.get("is_complete"), "Extracted multiple fields at once")
    },
    {
        "name": "Story Format",
        "messages": [
            "Well I used to be a quarterback so I'm a guy, born in 1990",
            "I'm 180 cm tall and weigh about 90 kg lately",
            "Trying to get back to my playing weight of 80 kg",
            "I work out moderately, gym 3x a week",
            "that looks perfect",
            "pescatarian actually"
        ],
        "check": lambda r: (r.get("is_complete") and r["collected_data"].get("pescatarian") == True, 
                           "Story format + pescatarian")
    },
    
    # --- Unit Variations ---
    {
        "name": "Imperial Units (feet/inches/lbs)",
        "messages": [
            "female, 30",
            "5 feet 6 inches, 150 pounds",
            "want to reach 140 lbs",
            "light activity",
            "yes perfect",
            "gluten free"
        ],
        "check": lambda r: (r.get("is_complete") and 
                           r["collected_data"].get("current_height_unit") in ["in", "ft"],
                           "Imperial units processed")
    },
    {
        "name": "Mixed Units (cm height + lbs weight)",
        "messages": [
            "male 28",
            "175 cm tall",
            "200 lbs currently",
            "want to get to 180 lbs, lose weight",
            "moderate",
            "yes",
            "none"
        ],
        "check": lambda r: (r.get("is_complete"), "Mixed metric/imperial")
    },
    
    # --- Date Format Variations ---
    {
        "name": "Wordy Date (June 15th 1995)",
        "messages": [
            "female",
            "born June 15th 1995",
            "165 cm 60 kg",
            "maintain weight",
            "sedentary",
            "looks good",
            "dairy free"
        ],
        "check": lambda r: ("1995" in str(r.get("collected_data", {}).get("date_of_birth", "")),
                           "Wordy date parsed")
    },
    
    # --- Dietary Preference Variations ---
    {
        "name": "Allergy Phrasing",
        "messages": [
            "male 25",
            "1990-01-01",
            "180 cm 80 kg",
            "maintain",
            "moderate",
            "yes",
            "I'm allergic to nuts and can't eat dairy"
        ],
        "check": lambda r: (r["collected_data"].get("nut_free") == True and 
                           r["collected_data"].get("dairy_free") == True,
                           "Allergy → dietary flags")
    },
    {
        "name": "Celiac Disease → Gluten Free",
        "messages": [
            "female 30",
            "1994-05-20",
            "170 cm 65 kg",
            "maintain",
            "light",
            "yes",
            "I have celiac disease"
        ],
        "check": lambda r: (r["collected_data"].get("gluten_free") == True,
                           "Celiac → gluten_free")
    },
    
    # --- Edge Behaviors ---
    {
        "name": "Self-Correction (170 wait 180)",
        "messages": [
            "male 25",
            "June 1995",
            "170 cm... wait I meant 180 cm, 85 kg",
            "lose weight to 75 kg",
            "moderate",
            "yes",
            "none"
        ],
        "check": lambda r: (r["collected_data"].get("current_height") == 180.0,
                           "Self-correction captured")
    },
    {
        "name": "Hesitant Goal (idk maybe lose)",
        "messages": [
            "male 28",
            "1996-03-15",
            "180 cm 90 kg",
            "idk maybe lose a bit? to 85 kg",
            "moderate",
            "yeah sure",
            "nope none"
        ],
        "check": lambda r: (r["collected_data"].get("goal") == "lose_weight",
                           "Hesitant goal parsed")
    },
    {
        "name": "Maintain Goal (auto-fill target)",
        "messages": [
            "female 25",
            "1999-01-01",
            "165 cm 55 kg",
            "just maintain my current weight",
            "active",
            "looks good",
            "vegan"
        ],
        "check": lambda r: (r["collected_data"].get("target_weight") == 55.0,
                           "Target auto-filled for maintain")
    },
]

def main():
    print("=" * 70)
    print("CONVERSATIONAL ONBOARDING - EDGE CASE TESTS")
    print("=" * 70)
    
    passed = 0
    failed = 0
    failed_cases = []
    
    for case in EDGE_CASES:
        try:
            success = run_edge_case(case["name"], case["messages"], case["check"])
            if success:
                passed += 1
            else:
                failed += 1
                failed_cases.append(case["name"])
        except Exception as e:
            print(f"   ❌ EXCEPTION: {e}")
            failed += 1
            failed_cases.append(case["name"])
    
    # Summary
    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    print(f"✅ Passed: {passed}/{len(EDGE_CASES)}")
    print(f"❌ Failed: {failed}/{len(EDGE_CASES)}")
    if failed_cases:
        print(f"\nFailed cases:")
        for name in failed_cases:
            print(f"   • {name}")
    print("=" * 70)

if __name__ == "__main__":
    main()
