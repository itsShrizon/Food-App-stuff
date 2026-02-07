#!/usr/bin/env python3
"""
Test script for the /api/v1/onboarding REST API endpoints.
Requires the FastAPI server to be running.
"""

import requests
import json
from datetime import date

BASE_URL = "http://localhost:8000/api/v1/onboarding"

def print_result(test_name: str, response: requests.Response, expected_status: int = 200):
    """Print formatted test result."""
    status = "✅ PASS" if response.status_code == expected_status else "❌ FAIL"
    print(f"\n{status} {test_name}")
    print(f"  Status: {response.status_code} (expected {expected_status})")
    try:
        print(f"  Response: {json.dumps(response.json(), indent=2, default=str)[:500]}")
    except:
        print(f"  Response: {response.text[:500]}")
    return response.status_code == expected_status

def test_get_nonexistent_profile():
    """Test GET for non-existent user."""
    r = requests.get(f"{BASE_URL}/99999")
    return print_result("GET non-existent profile", r, 404)

def test_post_nonexistent_user():
    """Test POST with non-existent user."""
    payload = {
        "user_id": 99999,
        "gender": "male",
        "date_of_birth": "1990-01-01",
        "current_height": 180,
        "current_height_unit": "cm",
        "current_weight": 80,
        "current_weight_unit": "kg",
        "target_weight": 75,
        "target_weight_unit": "kg",
        "goal": "lose_weight",
        "activity_level": "moderate"
    }
    r = requests.post(BASE_URL, json=payload)
    return print_result("POST with non-existent user", r, 404)

def test_post_valid_profile(user_id: int):
    """Test POST with valid data."""
    payload = {
        "user_id": user_id,
        "gender": "male",
        "date_of_birth": "1990-01-01",
        "current_height": 180,
        "current_height_unit": "cm",
        "current_weight": 80,
        "current_weight_unit": "kg",
        "target_weight": 75,
        "target_weight_unit": "kg",
        "goal": "lose_weight",
        "activity_level": "moderate"
    }
    r = requests.post(BASE_URL, json=payload)
    return print_result(f"POST valid profile for user {user_id}", r, 200)

def test_get_existing_profile(user_id: int):
    """Test GET for existing user."""
    r = requests.get(f"{BASE_URL}/{user_id}")
    return print_result(f"GET existing profile for user {user_id}", r, 200)

def test_post_with_dietary(user_id: int):
    """Test POST with dietary preferences."""
    payload = {
        "user_id": user_id,
        "gender": "female",
        "date_of_birth": "1995-06-15",
        "current_height": 165,
        "current_height_unit": "cm",
        "current_weight": 60,
        "current_weight_unit": "kg",
        "target_weight": 55,
        "target_weight_unit": "kg",
        "goal": "lose_weight",
        "activity_level": "active",
        "vegan": True,
        "gluten_free": True
    }
    r = requests.post(BASE_URL, json=payload)
    return print_result(f"POST with dietary preferences for user {user_id}", r, 200)

def test_post_maintain_goal(user_id: int):
    """Test POST with maintain goal."""
    payload = {
        "user_id": user_id,
        "gender": "male",
        "date_of_birth": "1985-03-20",
        "current_height": 175,
        "current_height_unit": "cm",
        "current_weight": 70,
        "current_weight_unit": "kg",
        "target_weight": 70,  # Same as current for maintain
        "target_weight_unit": "kg",
        "goal": "maintain",
        "activity_level": "light"
    }
    r = requests.post(BASE_URL, json=payload)
    return print_result(f"POST maintain goal for user {user_id}", r, 200)

def test_post_imperial_units(user_id: int):
    """Test POST with imperial units."""
    payload = {
        "user_id": user_id,
        "gender": "female",
        "date_of_birth": "2000-12-25",
        "current_height": 66,
        "current_height_unit": "in",
        "current_weight": 150,
        "current_weight_unit": "lb",
        "target_weight": 140,
        "target_weight_unit": "lb",
        "goal": "lose_weight",
        "activity_level": "moderate"
    }
    r = requests.post(BASE_URL, json=payload)
    return print_result(f"POST imperial units for user {user_id}", r, 200)

def test_post_gain_weight(user_id: int):
    """Test POST with gain weight goal."""
    payload = {
        "user_id": user_id,
        "gender": "male",
        "date_of_birth": "1998-07-10",
        "current_height": 185,
        "current_height_unit": "cm",
        "current_weight": 70,
        "current_weight_unit": "kg",
        "target_weight": 80,
        "target_weight_unit": "kg",
        "goal": "gain_weight",
        "activity_level": "active"
    }
    r = requests.post(BASE_URL, json=payload)
    return print_result(f"POST gain weight goal for user {user_id}", r, 200)

def main():
    print("=" * 60)
    print("ONBOARDING API TEST SUITE")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    
    # Check if server is running
    try:
        requests.get("http://localhost:8000/")
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Server not running. Start with: uvicorn app.main:app --reload")
        return
    
    results = []
    
    # Test 1: GET non-existent profile
    results.append(test_get_nonexistent_profile())
    
    # Test 2: POST with non-existent user
    results.append(test_post_nonexistent_user())
    
    # NOTE: For the following tests, we need an existing user_id in the database.
    # Using user_id=1 assuming it exists. If not, these will fail with 404.
    test_user_id = 1
    
    # Test 3: POST valid profile
    results.append(test_post_valid_profile(test_user_id))
    
    # Test 4: GET existing profile
    results.append(test_get_existing_profile(test_user_id))
    
    # Test 5: POST with dietary preferences
    results.append(test_post_with_dietary(test_user_id))
    
    # Test 6: POST with maintain goal
    results.append(test_post_maintain_goal(test_user_id))
    
    # Test 7: POST with imperial units
    results.append(test_post_imperial_units(test_user_id))
    
    # Test 8: POST with gain weight
    results.append(test_post_gain_weight(test_user_id))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️ Some tests failed. Check output above.")

if __name__ == "__main__":
    main()
