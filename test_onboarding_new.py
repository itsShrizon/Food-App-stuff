"""Test suite for the new AI-powered onboarding with macro recommendations."""

import json
from unittest.mock import MagicMock, patch

import pytest

from onboarding import (
    ONBOARDING_FIELDS,
    OPTIONAL_FIELDS,
    ACTIVITY_MULTIPLIERS,
    calculate_macros,
    onboarding,
    start_onboarding,
    _safe_parse_json,
    _validate_extracted_data,
    _parse_weight_to_kg,
    _parse_height_to_cm,
    _calculate_age,
    _extract_data_with_llm,
)


class TestSafeParseJson:
    """Tests for failsafe JSON parsing."""

    def test_valid_json(self):
        """Test parsing valid JSON."""
        result = _safe_parse_json('{"name": "test", "value": 123}')
        assert result == {"name": "test", "value": 123}

    def test_empty_string(self):
        """Test parsing empty string returns empty dict."""
        result = _safe_parse_json('')
        assert result == {}

    def test_none_input(self):
        """Test parsing None returns empty dict."""
        result = _safe_parse_json(None)
        assert result == {}

    def test_json_in_markdown_code_block(self):
        """Test extracting JSON from markdown code blocks."""
        response = '```json\n{"gender": "male"}\n```'
        result = _safe_parse_json(response)
        assert result == {"gender": "male"}

    def test_json_in_code_block_without_json_label(self):
        """Test extracting JSON from code block without json label."""
        response = '```\n{"age": 25}\n```'
        result = _safe_parse_json(response)
        assert result == {"age": 25}

    def test_malformed_json_fallback(self):
        """Test fallback for malformed JSON."""
        response = 'Some text {"key": "value"} more text'
        result = _safe_parse_json(response)
        assert result == {"key": "value"}

    def test_completely_invalid_returns_empty(self):
        """Test completely invalid input returns empty dict."""
        result = _safe_parse_json('this is not json at all')
        assert result == {}


class TestValidateExtractedData:
    """Tests for data validation failsafe."""

    def test_valid_gender_male(self):
        """Test validating male gender."""
        result = _validate_extracted_data({"gender": "male"})
        assert result["gender"] == "male"

    def test_gender_shorthand(self):
        """Test validating gender shorthand."""
        result = _validate_extracted_data({"gender": "m"})
        assert result["gender"] == "male"
        
        result = _validate_extracted_data({"gender": "f"})
        assert result["gender"] == "female"

    def test_invalid_gender_rejected(self):
        """Test invalid gender is rejected."""
        result = _validate_extracted_data({"gender": "invalid_value"})
        assert "gender" not in result

    def test_valid_date_of_birth(self):
        """Test validating date of birth."""
        result = _validate_extracted_data({"date_of_birth": "1990-05-15"})
        assert result["date_of_birth"] == "1990-05-15"

    def test_invalid_date_rejected(self):
        """Test invalid date is rejected."""
        result = _validate_extracted_data({"date_of_birth": "not-a-date"})
        assert "date_of_birth" not in result

    def test_valid_activity_level(self):
        """Test validating activity level."""
        for level in ACTIVITY_MULTIPLIERS.keys():
            result = _validate_extracted_data({"activity_level": level})
            assert result["activity_level"] == level

    def test_invalid_activity_level_rejected(self):
        """Test invalid activity level is rejected."""
        result = _validate_extracted_data({"activity_level": "super_active"})
        assert "activity_level" not in result

    def test_goal_normalization(self):
        """Test goal values are normalized."""
        result = _validate_extracted_data({"goal": "lose"})
        assert result["goal"] == "lose weight"
        
        result = _validate_extracted_data({"goal": "bulk"})
        assert result["goal"] == "gain weight"

    def test_weight_string_accepted(self):
        """Test weight strings are accepted."""
        result = _validate_extracted_data({"current_weight": "75 kg"})
        assert result["current_weight"] == "75 kg"

    def test_macros_confirmed_boolean(self):
        """Test macros_confirmed boolean handling."""
        result = _validate_extracted_data({"macros_confirmed": True})
        assert result["macros_confirmed"] is True
        
        result = _validate_extracted_data({"macros_confirmed": "yes"})
        assert result["macros_confirmed"] is True


class TestCalculateMacros:
    """Tests for macro calculation."""

    def test_basic_calculation(self):
        """Test basic macro calculation."""
        result = calculate_macros(
            gender="male",
            weight_kg=75,
            height_cm=175,
            age=30,
            activity_level="moderate",
            goal="maintain"
        )
        
        assert "calories" in result
        assert "protein_g" in result
        assert "carbs_g" in result
        assert "fat_g" in result
        assert result["calories"] > 0
        assert result["protein_g"] > 0

    def test_lose_weight_deficit(self):
        """Test that lose weight creates caloric deficit."""
        maintain = calculate_macros("male", 75, 175, 30, "moderate", "maintain")
        lose = calculate_macros("male", 75, 175, 30, "moderate", "lose weight")
        
        assert lose["calories"] < maintain["calories"]

    def test_gain_weight_surplus(self):
        """Test that gain weight creates caloric surplus."""
        maintain = calculate_macros("male", 75, 175, 30, "moderate", "maintain")
        gain = calculate_macros("male", 75, 175, 30, "moderate", "gain weight")
        
        assert gain["calories"] > maintain["calories"]

    def test_activity_level_affects_calories(self):
        """Test that higher activity means more calories."""
        sedentary = calculate_macros("male", 75, 175, 30, "sedentary", "maintain")
        active = calculate_macros("male", 75, 175, 30, "active", "maintain")
        
        assert active["calories"] > sedentary["calories"]

    def test_failsafe_invalid_weight(self):
        """Test failsafe for invalid weight uses default."""
        result = calculate_macros("male", "invalid", 175, 30, "moderate", "maintain")
        assert result["calories"] > 0  # Should not crash

    def test_failsafe_negative_weight(self):
        """Test failsafe for negative weight uses default."""
        result = calculate_macros("male", -50, 175, 30, "moderate", "maintain")
        assert result["calories"] > 0

    def test_failsafe_invalid_height(self):
        """Test failsafe for invalid height uses default."""
        result = calculate_macros("male", 75, "tall", 30, "moderate", "maintain")
        assert result["calories"] > 0

    def test_minimum_calories(self):
        """Test that calories don't go below minimum."""
        # Very low weight person trying to lose weight
        result = calculate_macros("female", 40, 150, 60, "sedentary", "lose weight")
        assert result["calories"] >= 1200


class TestParseWeightToKg:
    """Tests for weight parsing."""

    def test_kg_value(self):
        """Test parsing kg values."""
        assert _parse_weight_to_kg("75 kg") == 75.0
        assert _parse_weight_to_kg("75kg") == 75.0

    def test_lbs_value(self):
        """Test parsing lbs values."""
        result = _parse_weight_to_kg("165 lbs")
        assert 74 < result < 76  # ~74.84 kg

    def test_pounds_value(self):
        """Test parsing pounds values."""
        result = _parse_weight_to_kg("165 pounds")
        assert 74 < result < 76

    def test_plain_number(self):
        """Test parsing plain number assumes kg."""
        assert _parse_weight_to_kg("80") == 80.0

    def test_invalid_returns_default(self):
        """Test invalid input returns default."""
        assert _parse_weight_to_kg("heavy") == 70.0


class TestParseHeightToCm:
    """Tests for height parsing."""

    def test_cm_value(self):
        """Test parsing cm values."""
        assert _parse_height_to_cm("175 cm") == 175.0
        assert _parse_height_to_cm("175cm") == 175.0

    def test_feet_inches(self):
        """Test parsing feet and inches."""
        result = _parse_height_to_cm("5 foot 9 inches")
        assert 174 < result < 177  # ~175.26 cm

    def test_feet_only(self):
        """Test parsing feet only."""
        result = _parse_height_to_cm("6 feet")
        assert 182 < result < 184  # ~182.88 cm

    def test_short_format(self):
        """Test parsing short format like 5'9\"."""
        result = _parse_height_to_cm("5'9\"")
        assert 174 < result < 177

    def test_inches_only(self):
        """Test plain inches value gets converted."""
        result = _parse_height_to_cm("69")  # 69 inches
        assert 174 < result < 177

    def test_invalid_returns_default(self):
        """Test invalid input returns default."""
        assert _parse_height_to_cm("tall") == 170.0


class TestCalculateAge:
    """Tests for age calculation."""

    def test_valid_date(self):
        """Test age calculation from valid date."""
        # This will depend on current date, so we just check it's reasonable
        age = _calculate_age("1990-01-01")
        assert 30 < age < 40

    def test_invalid_date_returns_default(self):
        """Test invalid date returns default age."""
        assert _calculate_age("invalid") == 25


class TestOnboardingFlow:
    """Tests for the main onboarding flow."""

    @patch("onboarding.chatbot")
    def test_start_onboarding(self, mock_chatbot):
        """Test starting onboarding."""
        mock_chatbot.return_value = "Welcome! Let's get started!"
        
        result = start_onboarding()
        
        assert result["message"] == "Welcome! Let's get started!"
        assert result["is_complete"] is False
        assert result["collected_data"] == {}
        assert len(result["conversation_history"]) == 1

    @patch("onboarding.chatbot")
    def test_start_onboarding_failsafe(self, mock_chatbot):
        """Test start_onboarding failsafe when chatbot fails."""
        mock_chatbot.side_effect = Exception("API Error")
        
        result = start_onboarding()
        
        # Should not crash, should return fallback message
        assert result["is_complete"] is False
        assert "welcome" in result["message"].lower() or "hey" in result["message"].lower()

    @patch("onboarding.chatbot")
    def test_onboarding_extracts_data(self, mock_chatbot):
        """Test that onboarding extracts data from responses."""
        mock_chatbot.side_effect = [
            '{"gender": "male", "date_of_birth": "1990-05-15"}',  # extraction
            "Great! What's your height?"  # conversation
        ]
        
        result = onboarding("I'm a male born May 15, 1990")
        
        assert result["collected_data"].get("gender") == "male"
        assert result["collected_data"].get("date_of_birth") == "1990-05-15"

    @patch("onboarding.chatbot")
    def test_macro_calculation_triggered(self, mock_chatbot):
        """Test that macros are calculated when all required fields are present."""
        collected_data = {
            "gender": "male",
            "date_of_birth": "1990-01-01",
            "current_height": "175 cm",
            "current_weight": "75 kg",
            "target_weight": "70 kg",
            "goal": "lose weight",
            "activity_level": "moderate",
        }
        
        mock_chatbot.side_effect = [
            '{}',  # extraction (no new data)
            "Here are your recommended macros..."  # conversation
        ]
        
        result = onboarding(
            "I'm moderately active",
            collected_data=collected_data,
        )
        
        # Macros should be calculated
        assert "recommended_macros" in result["collected_data"]
        macros = result["collected_data"]["recommended_macros"]
        assert macros["calories"] > 0

    @patch("onboarding.chatbot")
    def test_onboarding_completion(self, mock_chatbot):
        """Test onboarding completes when all data collected and macros confirmed."""
        collected_data = {
            "gender": "male",
            "date_of_birth": "1990-01-01",
            "current_height": "175 cm",
            "current_weight": "75 kg",
            "target_weight": "70 kg",
            "goal": "lose weight",
            "activity_level": "moderate",
            "recommended_macros": {"calories": 2000, "protein_g": 135, "carbs_g": 200, "fat_g": 55},
            "macros_confirmed": True,
            "dietary_preference": "none",
            "allergies": "none",
            "extra_notes": "none",
        }
        
        mock_chatbot.return_value = '{}'
        
        result = onboarding(
            "No extras",
            collected_data=collected_data,
        )
        
        assert result["is_complete"] is True
        assert "complete" in result["message"].lower()

    @patch("onboarding.chatbot")
    def test_skip_optional_fields(self, mock_chatbot):
        """Test that saying 'skip' completes optional fields."""
        collected_data = {
            "gender": "male",
            "date_of_birth": "1990-01-01",
            "current_height": "175 cm",
            "current_weight": "75 kg",
            "target_weight": "70 kg",
            "goal": "lose weight",
            "activity_level": "moderate",
            "recommended_macros": {"calories": 2000, "protein_g": 135, "carbs_g": 200, "fat_g": 55},
            "macros_confirmed": True,
        }
        
        mock_chatbot.return_value = '{}'
        
        result = onboarding(
            "skip",
            collected_data=collected_data,
        )
        
        assert result["is_complete"] is True

    @patch("onboarding.chatbot")
    def test_chatbot_error_failsafe(self, mock_chatbot):
        """Test failsafe when chatbot throws error."""
        collected_data = {
            "gender": "male",
        }
        
        mock_chatbot.side_effect = [
            '{}',  # extraction succeeds
            Exception("API Error")  # conversation fails
        ]
        
        result = onboarding(
            "test message",
            collected_data=collected_data,
        )
        
        # Should not crash, should return fallback message
        assert result["is_complete"] is False
        assert result["message"]  # Should have some response


class TestOnboardingFieldsIntegrity:
    """Tests for field definitions."""

    def test_required_fields_defined(self):
        """Test all required fields are defined."""
        expected = (
            'gender', 'date_of_birth', 'current_height', 
            'current_weight', 'target_weight', 'goal', 'activity_level'
        )
        assert ONBOARDING_FIELDS == expected

    def test_optional_fields_defined(self):
        """Test optional fields are defined."""
        assert 'dietary_preference' in OPTIONAL_FIELDS
        assert 'allergies' in OPTIONAL_FIELDS
        assert 'extra_notes' in OPTIONAL_FIELDS

    def test_activity_multipliers_defined(self):
        """Test all activity multipliers are defined."""
        expected_levels = ['sedentary', 'light', 'moderate', 'active']
        for level in expected_levels:
            assert level in ACTIVITY_MULTIPLIERS
            assert ACTIVITY_MULTIPLIERS[level] > 0


class TestEndToEndScenarios:
    """End-to-end scenario tests."""

    @patch("onboarding.chatbot")
    def test_full_flow_happy_path(self, mock_chatbot):
        """Test complete onboarding flow."""
        mock_chatbot.side_effect = [
            "Welcome!",  # start_onboarding
            # First message - basic info
            '{"gender": "male", "date_of_birth": "1990-05-15"}',
            "What's your height?",
            # Second message - measurements
            '{"gender": "male", "date_of_birth": "1990-05-15", "current_height": "175 cm", "current_weight": "75 kg", "target_weight": "70 kg"}',
            "What's your goal?",
            # Third message - goal and activity
            '{"gender": "male", "date_of_birth": "1990-05-15", "current_height": "175 cm", "current_weight": "75 kg", "target_weight": "70 kg", "goal": "lose weight", "activity_level": "moderate"}',
            "Here are your macros...",
            # Fourth message - confirm macros
            '{"macros_confirmed": true}',
            "Great! Any dietary preferences?",
            # Fifth message - finish
            '{"dietary_preference": "none", "allergies": "none"}',
            "All done!",
        ]
        
        # Start
        result = start_onboarding()
        assert not result["is_complete"]
        
        # Provide basic info
        result = onboarding("I'm male, born May 15 1990", 
                           conversation_history=result["conversation_history"],
                           collected_data=result["collected_data"])
        assert "gender" in result["collected_data"]
        
        # Provide measurements
        result = onboarding("175 cm, 75 kg, want to reach 70 kg",
                           conversation_history=result["conversation_history"],
                           collected_data=result["collected_data"])
        
        # Provide goal and activity
        result = onboarding("I want to lose weight, moderate activity",
                           conversation_history=result["conversation_history"],
                           collected_data=result["collected_data"])
        
        # Should have calculated macros
        assert "recommended_macros" in result["collected_data"]
        
        # Confirm macros
        result = onboarding("Yes, looks good",
                           conversation_history=result["conversation_history"],
                           collected_data=result["collected_data"])
        
        # Skip optional
        result = onboarding("No dietary restrictions, no allergies",
                           conversation_history=result["conversation_history"],
                           collected_data=result["collected_data"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
