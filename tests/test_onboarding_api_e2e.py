#!/usr/bin/env python3
"""
End-to-End API Test for /api/v1/onboarding endpoints.
Tests the full workflow: POST profile -> GET profile -> verify calculations.
"""

import requests
import json
from datetime import date

BASE_URL = "http://localhost:8000/api/v1/onboarding"

# Test scenarios with different user profiles
SCENARIOS = [
    {
        "name": "Male Lose Weight (Metric)",
        "data": {
            "user_id": 1,
            "gender": "male",
            "date_of_birth": "1990-01-15",
            "current_height": 180,
            "current_height_unit": "cm",
            "current_weight": 90,
            "current_weight_unit": "kg",
            "target_weight": 80,
            "target_weight_unit": "kg",
            "goal": "lose_weight",
            "activity_level": "moderate"
        },
        "expected": {"goal": "lose_weight", "deficit": True}
    },
    {
        "name": "Female Gain Weight (Metric)",
        "data": {
            "user_id": 1,
            "gender": "female",
            "date_of_birth": "1995-06-20",
            "current_height": 165,
            "current_height_unit": "cm",
            "current_weight": 55,
            "current_weight_unit": "kg",
            "target_weight": 60,
            "target_weight_unit": "kg",
            "goal": "gain_weight",
            "activity_level": "light"
        },
        "expected": {"goal": "gain_weight", "surplus": True}
    },
    {
        "name": "Male Maintain (Imperial)",
        "data": {
            "user_id": 1,
            "gender": "male", 
            "date_of_birth": "1988-03-10",
            "current_height": 70,
            "current_height_unit": "in",
            "current_weight": 180,
            "current_weight_unit": "lb",
            "target_weight": 180,
            "target_weight_unit": "lb",
            "goal": "maintain",
            "activity_level": "active"
        },
        "expected": {"goal": "maintain", "tdee_equals_target": True}
    },
    {
        "name": "Vegan + Gluten Free Diet",
        "data": {
            "user_id": 1,
            "gender": "male",
            "date_of_birth": "1990-01-15",
            "current_height": 180,
            "current_height_unit": "cm",
            "current_weight": 85,
            "current_weight_unit": "kg",
            "target_weight": 80,
            "target_weight_unit": "kg",
            "goal": "lose_weight",
            "activity_level": "moderate",
            "vegan": True,
            "gluten_free": True
        },
        "expected": {"vegan": True, "gluten_free": True}
    },
    {
        "name": "Others Gender Maintain",
        "data": {
            "user_id": 1,
            "gender": "others",
            "date_of_birth": "2000-12-25",
            "current_height": 170,
            "current_height_unit": "cm",
            "current_weight": 70,
            "current_weight_unit": "kg",
            "target_weight": 70,
            "target_weight_unit": "kg",
            "goal": "maintain",
            "activity_level": "sedentary"
        },
        "expected": {"goal": "maintain"}
    }
]


def test_scenario(scenario):
    """Run a single test scenario."""
    name = scenario["name"]
    data = scenario["data"]
    expected = scenario["expected"]
    
    print(f"\n{'='*60}")
    print(f"SCENARIO: {name}")
    print(f"{'='*60}")
    
    # Step 1: POST - Create/Update profile
    print("\n📤 POST /api/v1/onboarding/")
    print(f"   Request: {json.dumps(data, indent=2, default=str)}")
    
    try:
        resp = requests.post(f"{BASE_URL}/", json=data)
    except requests.exceptions.ConnectionError:
        print("❌ FAILED: Could not connect to server. Is it running?")
        return False
    
    print(f"   Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAILED: Expected 200, got {resp.status_code}")
        print(f"   Response: {resp.text}")
        return False
    
    post_result = resp.json()
    print(f"   Response: {json.dumps(post_result, indent=2, default=str)[:500]}...")
    
    # Verify metabolic profile exists
    if "metabolic" not in post_result and "warning" in post_result:
        print(f"⚠️  WARNING: {post_result.get('warning')}")
    elif "metabolic" in post_result:
        metabolic = post_result["metabolic"]
        print(f"\n   📊 Metabolic Calculations:")
        print(f"      BMR: {metabolic.get('bmr')} kcal")
        print(f"      TDEE: {metabolic.get('tdee')} kcal")
        print(f"      Daily Target: {metabolic.get('daily_calorie_target')} kcal")
        print(f"      Protein: {metabolic.get('protein_g')}g | Carbs: {metabolic.get('carbs_g')}g | Fat: {metabolic.get('fats_g')}g")
        
        # Verify goal-based logic
        tdee = metabolic.get('tdee', 0)
        target = metabolic.get('daily_calorie_target', 0)
        
        if expected.get("deficit"):
            if target < tdee:
                print(f"   ✅ Deficit confirmed: {target} < {tdee}")
            else:
                print(f"   ❌ Expected deficit but target >= TDEE")
                return False
        
        if expected.get("surplus"):
            if target > tdee:
                print(f"   ✅ Surplus confirmed: {target} > {tdee}")
            else:
                print(f"   ❌ Expected surplus but target <= TDEE")
                return False
        
        if expected.get("tdee_equals_target"):
            if abs(target - tdee) < 0.1:
                print(f"   ✅ Maintain confirmed: Target ≈ TDEE")
            else:
                print(f"   ❌ Expected maintain but target != TDEE")
                return False
    
    # Step 2: GET - Fetch the profile back
    user_id = data["user_id"]
    print(f"\n📥 GET /api/v1/onboarding/{user_id}")
    
    resp = requests.get(f"{BASE_URL}/{user_id}")
    print(f"   Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAILED: Expected 200, got {resp.status_code}")
        return False
    
    get_result = resp.json()
    
    # Verify data matches
    if get_result.get("gender") == data["gender"]:
        print(f"   ✅ Gender matches: {data['gender']}")
    else:
        print(f"   ❌ Gender mismatch")
        return False
    
    if get_result.get("goal") == data["goal"]:
        print(f"   ✅ Goal matches: {data['goal']}")
    else:
        print(f"   ❌ Goal mismatch")
        return False
    
    # Check dietary preferences if specified
    if expected.get("vegan"):
        if get_result.get("vegan") == True:
            print(f"   ✅ Vegan preference saved")
        else:
            print(f"   ❌ Vegan not saved")
            return False
    
    if expected.get("gluten_free"):
        if get_result.get("gluten_free") == True:
            print(f"   ✅ Gluten-free preference saved")
        else:
            print(f"   ❌ Gluten-free not saved")
            return False
    
    print(f"\n✅ SCENARIO PASSED: {name}")
    return True

def test_error_cases():
    """Test error handling."""
    print(f"\n{'='*60}")
    print("ERROR HANDLING TESTS")
    print(f"{'='*60}")
    
    passed = 0
    failed = 0
    
    # Test 1: GET non-existent profile
    print("\n📥 GET /api/v1/onboarding/99999 (non-existent)")
    resp = requests.get(f"{BASE_URL}/99999")
    if resp.status_code == 404:
        print(f"   ✅ Correctly returned 404")
        passed += 1
    else:
        print(f"   ❌ Expected 404, got {resp.status_code}")
        failed += 1
    
    # Test 2: POST with non-existent user
    print("\n📤 POST with user_id=99999 (non-existent user)")
    resp = requests.post(f"{BASE_URL}/", json={
        "user_id": 99999,
        "gender": "male",
        "date_of_birth": "1990-01-01",
        "current_height": 180,
        "current_weight": 80,
        "target_weight": 75,
        "goal": "lose_weight",
        "activity_level": "moderate"
    })
    if resp.status_code == 404:
        print(f"   ✅ Correctly returned 404 (User not found)")
        passed += 1
    else:
        print(f"   ❌ Expected 404, got {resp.status_code}")
        failed += 1
    
    return passed, failed

def main():
    print("="*60)
    print("ONBOARDING API E2E TEST SUITE")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    
    passed = 0
    failed = 0
    
    # Run main scenarios
    for scenario in SCENARIOS:
        try:
            if test_scenario(scenario):
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            failed += 1
    
    # Run error cases
    error_passed, error_failed = test_error_cases()
    passed += error_passed
    failed += error_failed
    
    # Summary
    total = passed + failed
    print(f"\n{'='*60}")
    print("FINAL RESULTS")
    print(f"{'='*60}")
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {failed}/{total}")
    print(f"{'='*60}")
    
    return failed == 0

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
