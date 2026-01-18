"""Test dynamic dietary extraction in onboarding flow."""

import unittest
from unittest.mock import patch, MagicMock
import json

from onboarding.flow import onboarding
from onboarding.config import ONBOARDING_FIELDS

# Mocking DIETARY_PREFERENCE_FLAGS for validation in tests if needed, 
# but we trust the constants in the module.

class TestDynamicDietary(unittest.TestCase):
    
    @patch("onboarding.service.chatbot")
    def test_extract_dietary_vegan(self, mock_chatbot):
        """Test correct extraction of vegan preference using LLM."""
        collected = {f: "val" for f in ONBOARDING_FIELDS}
        collected["macros_confirmed"] = True
        
        mock_chatbot.return_value = json.dumps({
            "dietary": ["vegan"]
        })
        
        result = onboarding(
            "I am vegan",
            collected_data=collected,
            conversation_history=[]
        )
        
        self.assertTrue(result["collected_data"].get("vegan"))
        self.assertIsNone(result["collected_data"].get("dairy_free"))
        
    @patch("onboarding.service.chatbot")
    def test_extract_dietary_none(self, mock_chatbot):
        """Test extraction when user says they have no restrictions."""
        collected = {f: "val" for f in ONBOARDING_FIELDS}
        collected["macros_confirmed"] = True
        
        mock_chatbot.return_value = json.dumps({
            "dietary": ["none"]
        })
        
        result = onboarding(
            "No restrictions",
            collected_data=collected,
            conversation_history=[]
        )
        
        self.assertTrue(result["collected_data"].get("dietary_none_stated"))
        self.assertTrue(result["is_complete"])
        
    @patch("onboarding.service.chatbot")
    def test_extract_dietary_multiple(self, mock_chatbot):
        """Test extraction of multiple preferences."""
        collected = {f: "val" for f in ONBOARDING_FIELDS}
        collected["macros_confirmed"] = True
        
        mock_chatbot.return_value = json.dumps({
            "dietary": ["gluten_free", "nut_free"]
        })
        
        result = onboarding(
            "I'm gluten free and allergic to nuts",
            collected_data=collected,
            conversation_history=[]
        )
        
        self.assertTrue(result["collected_data"].get("gluten_free"))
        self.assertTrue(result["collected_data"].get("nut_free"))
        self.assertIsNone(result["collected_data"].get("vegan"))

    @patch("onboarding.service.chatbot")
    def test_dietary_mapped_values(self, mock_chatbot):
        """Test mapping of variations like 'dairy' to 'dairy_free'."""
        collected = {f: "val" for f in ONBOARDING_FIELDS}
        collected["macros_confirmed"] = True
        
        # validators.py maps 'dairy' -> 'dairy_free'
        mock_chatbot.return_value = json.dumps({
            "dietary": ["dairy"] 
        })
        
        result = onboarding(
            "No dairy",
            collected_data=collected,
            conversation_history=[]
        )
        
        self.assertTrue(result["collected_data"].get("dairy_free"))

if __name__ == "__main__":
    unittest.main()
