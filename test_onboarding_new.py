"""Test suite for layered onboarding architecture."""

from unittest.mock import patch
import pytest

from onboarding import (
    ONBOARDING_FIELDS,
    DIETARY_PREFERENCE_FLAGS,
)
from onboarding.utils import safe_parse_json, calculate_age, convert_weight_to_kg, convert_height_to_cm
from onboarding.validators import validate_extracted_data
from onboarding.calculator import calculate_metabolic_profile
from onboarding.formatter import format_output_for_db, build_dietary_preferences
from onboarding.flow import onboarding
from onboarding.start import start_onboarding


class TestConfig:
    def test_fields(self):
        assert len(ONBOARDING_FIELDS) == 11
        assert 'gender' in ONBOARDING_FIELDS
    
    def test_dietary_flags(self):
        assert 'vegan' in DIETARY_PREFERENCE_FLAGS
        assert len(DIETARY_PREFERENCE_FLAGS) == 5


class TestUtils:
    def test_safe_parse_json(self):
        assert safe_parse_json('{"a": 1}') == {"a": 1}
        assert safe_parse_json('invalid') == {}
    
    def test_calculate_age(self):
        assert 25 <= calculate_age('1994-05-15') <= 35
        assert calculate_age('invalid') == 25
    
    def test_convert_weight(self):
        assert convert_weight_to_kg(75, 'kg') == 75
        assert 74 < convert_weight_to_kg(165, 'lb') < 76
    
    def test_convert_height(self):
        assert convert_height_to_cm(175, 'cm') == 175
        assert 174 < convert_height_to_cm(69, 'in') < 177


class TestValidators:
    def test_gender(self):
        assert validate_extracted_data({'gender': 'm'})['gender'] == 'male'
        assert 'gender' not in validate_extracted_data({'gender': 'invalid'})
    
    def test_goal(self):
        assert validate_extracted_data({'goal': 'lose'})['goal'] == 'lose_weight'
    
    def test_numeric(self):
        assert validate_extracted_data({'current_height': '175'})['current_height'] == 175.0


class TestCalculator:
    def test_basic(self):
        mp = calculate_metabolic_profile('male', 75, 'kg', 175, 'cm', 30, 'moderate', 'lose_weight', 70, 'kg')
        assert mp['daily_calorie_target'] > 0
        assert mp['protein_g'] > 0
        assert mp['estimated_weeks_to_goal'] == 10.0
    
    def test_deficit(self):
        maintain = calculate_metabolic_profile('male', 75, 'kg', 175, 'cm', 30, 'moderate', 'maintain', 75, 'kg')
        lose = calculate_metabolic_profile('male', 75, 'kg', 175, 'cm', 30, 'moderate', 'lose_weight', 70, 'kg')
        assert lose['daily_calorie_target'] < maintain['daily_calorie_target']


class TestFormatter:
    def test_db_format(self):
        output = format_output_for_db({'gender': 'male', 'goal': 'lose_weight'})
        assert 'onboarding' in output
        assert 'metabolic_profile' in output
        assert output['onboarding']['dietary_preferences']['vegan'] is False
    
    def test_dietary_prefs(self):
        prefs = build_dietary_preferences({'vegan': True})
        assert prefs['vegan'] is True
        assert prefs['dairy_free'] is False


class TestFlow:
    @patch('onboarding.start.chatbot')
    def test_start(self, mock):
        mock.return_value = 'Welcome!'
        result = start_onboarding()
        assert result['is_complete'] is False
        assert result['collected_data'] == {}
    
    @patch('onboarding.flow.chatbot')
    @patch('onboarding.service.chatbot')
    def test_onboarding(self, mock_service, mock_flow):
        mock_service.return_value = '{"gender": "male"}'
        mock_flow.return_value = 'Next question'
        result = onboarding('I am male')
        assert result['is_complete'] is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
