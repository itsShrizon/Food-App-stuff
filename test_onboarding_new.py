"""Test suite for AI-powered onboarding matching DB structure."""

import json
from unittest.mock import MagicMock, patch

import pytest

from onboarding import (
    ONBOARDING_FIELDS,
    DIETARY_PREFERENCE_FLAGS,
    ACTIVITY_MULTIPLIERS,
    TARGET_SPEED_RATES,
    calculate_metabolic_profile,
    onboarding,
    start_onboarding,
    format_output_for_db,
    _safe_parse_json,
    _validate_extracted_data,
    _convert_weight_to_kg,
    _convert_height_to_cm,
    _calculate_age,
    _build_dietary_preferences,
)


class TestSafeParseJson:
    """Tests for failsafe JSON parsing."""

    def test_valid_json(self):
        result = _safe_parse_json('{"name": "test", "value": 123}')
        assert result == {"name": "test", "value": 123}

    def test_empty_string(self):
        result = _safe_parse_json('')
        assert result == {}

    def test_none_input(self):
        result = _safe_parse_json(None)
        assert result == {}

    def test_json_in_markdown_code_block(self):
        response = '```json\n{"gender": "male"}\n```'
        result = _safe_parse_json(response)
        assert result == {"gender": "male"}

    def test_malformed_json_fallback(self):
        response = 'Some text {"key": "value"} more text'
        result = _safe_parse_json(response)
        assert result == {"key": "value"}

    def test_completely_invalid_returns_empty(self):
        result = _safe_parse_json('this is not json at all')
        assert result == {}


class TestValidateExtractedData:
    """Tests for data validation."""

    def test_valid_gender(self):
        result = _validate_extracted_data({"gender": "male"})
        assert result["gender"] == "male"

    def test_gender_shorthand(self):
        result = _validate_extracted_data({"gender": "m"})
        assert result["gender"] == "male"

    def test_invalid_gender_rejected(self):
        result = _validate_extracted_data({"gender": "invalid"})
        assert "gender" not in result

    def test_goal_normalization(self):
        result = _validate_extracted_data({"goal": "lose weight"})
        assert result["goal"] == "lose_weight"
        
        result = _validate_extracted_data({"goal": "bulk"})
        assert result["goal"] == "gain_weight"

    def test_numeric_extraction(self):
        result = _validate_extracted_data({"current_height": "175"})
        assert result["current_height"] == 175.0

    def test_height_unit_normalization(self):
        result = _validate_extracted_data({"current_height_unit": "inches"})
        assert result["current_height_unit"] == "in"
        
        result = _validate_extracted_data({"current_height_unit": "cm"})
        assert result["current_height_unit"] == "cm"

    def test_weight_unit_normalization(self):
        result = _validate_extracted_data({"current_weight_unit": "lbs"})
        assert result["current_weight_unit"] == "lb"
        
        result = _validate_extracted_data({"current_weight_unit": "kg"})
        assert result["current_weight_unit"] == "kg"

    def test_dietary_preferences(self):
        result = _validate_extracted_data({"vegan": True, "dairy_free": "yes"})
        assert result["vegan"] is True
        assert result["dairy_free"] is True

    def test_target_speed(self):
        result = _validate_extracted_data({"target_speed": "fast"})
        assert result["target_speed"] == "fast"


class TestUnitConversions:
    """Tests for unit conversion functions."""

    def test_weight_lb_to_kg(self):
        result = _convert_weight_to_kg(165, 'lb')
        assert 74 < result < 76

    def test_weight_kg_unchanged(self):
        result = _convert_weight_to_kg(75, 'kg')
        assert result == 75

    def test_height_in_to_cm(self):
        result = _convert_height_to_cm(69, 'in')
        assert 174 < result < 177

    def test_height_cm_unchanged(self):
        result = _convert_height_to_cm(175, 'cm')
        assert result == 175


class TestCalculateMetabolicProfile:
    """Tests for metabolic profile calculation."""

    def test_basic_calculation(self):
        result = calculate_metabolic_profile(
            gender="male",
            weight=75, weight_unit="kg",
            height=175, height_unit="cm",
            age=30,
            activity_level="moderate",
            goal="maintain",
            target_weight=75, target_weight_unit="kg"
        )
        
        assert "daily_calorie_target" in result
        assert "protein_g" in result
        assert "carbs_g" in result
        assert "fats_g" in result
        assert "tdee" in result
        assert "bmr" in result
        assert "estimated_weeks_to_goal" in result

    def test_lose_weight_deficit(self):
        maintain = calculate_metabolic_profile(
            "male", 75, "kg", 175, "cm", 30, "moderate", "maintain", 75, "kg"
        )
        lose = calculate_metabolic_profile(
            "male", 75, "kg", 175, "cm", 30, "moderate", "lose_weight", 70, "kg"
        )
        
        assert lose["daily_calorie_target"] < maintain["daily_calorie_target"]

    def test_gain_weight_surplus(self):
        maintain = calculate_metabolic_profile(
            "male", 75, "kg", 175, "cm", 30, "moderate", "maintain", 75, "kg"
        )
        gain = calculate_metabolic_profile(
            "male", 75, "kg", 175, "cm", 30, "moderate", "gain_weight", 80, "kg"
        )
        
        assert gain["daily_calorie_target"] > maintain["daily_calorie_target"]

    def test_estimated_weeks_calculation(self):
        result = calculate_metabolic_profile(
            "male", 75, "kg", 175, "cm", 30, "moderate", "lose_weight",
            70, "kg", target_speed="normal"
        )
        # 5kg difference / 0.5kg per week = 10 weeks
        assert result["estimated_weeks_to_goal"] == 10.0

    def test_maintain_zero_weeks(self):
        result = calculate_metabolic_profile(
            "male", 75, "kg", 175, "cm", 30, "moderate", "maintain", 75, "kg"
        )
        assert result["estimated_weeks_to_goal"] == 0.0

    def test_imperial_units(self):
        result = calculate_metabolic_profile(
            "male", 165, "lb", 69, "in", 30, "moderate", "maintain", 165, "lb"
        )
        assert result["daily_calorie_target"] > 0
        assert result["bmr"] > 0


class TestDietaryPreferences:
    """Tests for dietary preferences handling."""

    def test_default_preferences(self):
        from onboarding import _get_default_dietary_preferences
        prefs = _get_default_dietary_preferences()
        
        for flag in DIETARY_PREFERENCE_FLAGS:
            assert flag in prefs
            assert prefs[flag] is False

    def test_build_preferences(self):
        collected = {"vegan": True, "dairy_free": True}
        prefs = _build_dietary_preferences(collected)
        
        assert prefs["vegan"] is True
        assert prefs["dairy_free"] is True
        assert prefs["gluten_free"] is False


class TestFormatOutputForDB:
    """Tests for DB format output."""

    def test_complete_output(self):
        collected = {
            'gender': 'male',
            'date_of_birth': '1994-05-15',
            'current_height': 175,
            'current_height_unit': 'cm',
            'current_weight': 75,
            'current_weight_unit': 'kg',
            'target_weight': 70,
            'target_weight_unit': 'kg',
            'goal': 'lose_weight',
            'target_speed': 'normal',
            'activity_level': 'moderate',
            'vegan': False,
            'dairy_free': True,
            'metabolic_profile': {
                'daily_calorie_target': 2000,
                'protein_g': 135,
                'carbs_g': 200,
                'fats_g': 60,
                'tdee': 2400,
                'bmr': 1700,
                'estimated_weeks_to_goal': 10,
            }
        }
        
        result = format_output_for_db(collected)
        
        assert 'onboarding' in result
        assert 'metabolic_profile' in result
        
        onboarding = result['onboarding']
        assert onboarding['gender'] == 'male'
        assert onboarding['current_height'] == 175
        assert onboarding['current_height_unit'] == 'cm'
        assert 'dietary_preferences' in onboarding
        assert onboarding['dietary_preferences']['dairy_free'] is True
        assert onboarding['dietary_preferences']['vegan'] is False

    def test_defaults_for_missing_fields(self):
        result = format_output_for_db({})
        
        assert result['onboarding']['current_height'] == 0
        assert result['onboarding']['goal'] == 'maintain'


class TestOnboardingFlow:
    """Tests for onboarding flow."""

    @patch("onboarding.chatbot")
    def test_start_onboarding(self, mock_chatbot):
        mock_chatbot.return_value = "Welcome! Let's get started!"
        
        result = start_onboarding()
        
        assert result["is_complete"] is False
        assert result["collected_data"] == {}
        assert result["db_format"] is None

    @patch("onboarding.chatbot")
    def test_start_onboarding_failsafe(self, mock_chatbot):
        mock_chatbot.side_effect = Exception("API Error")
        
        result = start_onboarding()
        
        # Should not crash
        assert result["is_complete"] is False
        assert "message" in result

    @patch("onboarding.chatbot")
    def test_metabolic_profile_calculated(self, mock_chatbot):
        collected_data = {
            "gender": "male",
            "date_of_birth": "1990-01-01",
            "current_height": 175,
            "current_height_unit": "cm",
            "current_weight": 75,
            "current_weight_unit": "kg",
            "target_weight": 70,
            "target_weight_unit": "kg",
            "goal": "lose_weight",
            "activity_level": "moderate",
        }
        
        mock_chatbot.side_effect = ['{}', "Here are your macros..."]
        
        result = onboarding("test", collected_data=collected_data)
        
        assert "metabolic_profile" in result["collected_data"]
        mp = result["collected_data"]["metabolic_profile"]
        assert mp["daily_calorie_target"] > 0
        assert mp["estimated_weeks_to_goal"] == 10.0

    @patch("onboarding.chatbot")
    def test_completion_returns_db_format(self, mock_chatbot):
        collected_data = {
            "gender": "male",
            "date_of_birth": "1990-01-01",
            "current_height": 175,
            "current_height_unit": "cm",
            "current_weight": 75,
            "current_weight_unit": "kg",
            "target_weight": 70,
            "target_weight_unit": "kg",
            "goal": "lose_weight",
            "target_speed": "normal",
            "activity_level": "moderate",
            "macros_confirmed": True,
            "vegan": False,
            "metabolic_profile": {
                'daily_calorie_target': 2000,
                'protein_g': 135, 'carbs_g': 200, 'fats_g': 60,
                'tdee': 2400, 'bmr': 1700, 'estimated_weeks_to_goal': 10,
            },
        }
        
        mock_chatbot.return_value = '{}'
        
        result = onboarding("no preferences", collected_data=collected_data)
        
        assert result["is_complete"] is True
        assert result["db_format"] is not None
        assert "onboarding" in result["db_format"]
        assert "metabolic_profile" in result["db_format"]


class TestFieldDefinitions:
    """Tests for field definitions matching DB schema."""

    def test_required_fields(self):
        expected = (
            'gender', 'date_of_birth',
            'current_height', 'current_height_unit',
            'current_weight', 'current_weight_unit',
            'target_weight', 'target_weight_unit',
            'goal', 'target_speed', 'activity_level',
        )
        assert ONBOARDING_FIELDS == expected

    def test_dietary_flags(self):
        expected = ('vegan', 'dairy_free', 'gluten_free', 'nut_free', 'pescatarian')
        assert DIETARY_PREFERENCE_FLAGS == expected

    def test_target_speeds(self):
        assert 'slow' in TARGET_SPEED_RATES
        assert 'normal' in TARGET_SPEED_RATES
        assert 'fast' in TARGET_SPEED_RATES


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
