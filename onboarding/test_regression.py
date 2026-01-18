"""Regression tests for onboarding flow using unittest."""

import unittest
from unittest.mock import patch, MagicMock
import json

from onboarding.flow import onboarding
from onboarding.start import start_onboarding
from onboarding.config import ONBOARDING_FIELDS

class TestOnboardingRegression(unittest.TestCase):
    
    @patch("onboarding.start.chatbot")
    def test_start_onboarding(self, mock_chatbot):
        """Test starting the onboarding process."""
        mock_chatbot.return_value = "Welcome! What is your gender?"
        
        result = start_onboarding()
        
        self.assertEqual(result["message"], "Welcome! What is your gender?")
        self.assertFalse(result["is_complete"])
        self.assertEqual(result["collected_data"], {})
        self.assertEqual(result["next_field"], "gender")
        
    @patch("onboarding.service.chatbot")
    def test_onboarding_basic_flow(self, mock_chatbot):
        """Test basic data collection."""
        # Mock extraction of gender
        mock_chatbot.return_value = json.dumps({"gender": "male"})
        
        conversation_history = [{"role": "assistant", "content": "Welcome!"}]
        
        result = onboarding(
            "I am male",
            collected_data={},
            conversation_history=conversation_history
        )
        
        self.assertEqual(result["collected_data"]["gender"], "male")
        self.assertFalse(result["is_complete"])
        
    @patch("onboarding.service.chatbot")
    def test_onboarding_completion(self, mock_chatbot):
        """Test completion when all fields are gathered."""
        collected = {
            "gender": "male",
            "date_of_birth": "1990-01-01",
            "current_height": 180, "current_height_unit": "cm",
            "current_weight": 80, "current_weight_unit": "kg",
            "target_weight": 75, "target_weight_unit": "kg",
            "goal": "lose_weight",
            "target_speed": "normal",
            "activity_level": "moderate",
            "macros_confirmed": True,
            # Dietary is optional/handled via flag or none
        }
        # Mark dietary as done via 'none' extraction
        collected["dietary_none_stated"] = True
        
        # When called with all data, LLM might extract nothing new
        mock_chatbot.return_value = "{}"
        
        result = onboarding(
            "Confirmed",
            collected_data=collected,
            conversation_history=[]
        )
        
        self.assertTrue(result["is_complete"])
        self.assertIn("Thank you", result["message"])
        self.assertIn("metabolic_profile", result)

    @patch("onboarding.service.chatbot")
    def test_validators_integration(self, mock_chatbot):
        """Test that validators sanitizes input."""
        # LLM returns messy data
        mock_chatbot.return_value = json.dumps({
            "gender": "  MALE  ",
            "current_weight": "80kgs",
        })
        
        result = onboarding(
            "Male, 80kg",
            collected_data={},
            conversation_history=[]
        )
        
        self.assertEqual(result["collected_data"]["gender"], "male")
        self.assertEqual(result["collected_data"]["current_weight"], 80.0)
        self.assertEqual(result["collected_data"]["current_weight_unit"], "kg")

if __name__ == "__main__":
    unittest.main()
