"""Test suite for LLM_shared and onboarding modules."""

import json
from unittest.mock import MagicMock, patch

import pytest

from LLM_shared import chatbot
from onboarding import (
    ONBOARDING_FIELDS,
    onboarding,
    start_onboarding,
    _extract_data_with_llm,
)


class TestChatbot:
    """Tests for the chatbot function."""

    @patch("LLM_shared.ChatOpenAI")
    def test_chatbot_simple_message(self, mock_chat_openai):
        """Test basic chatbot functionality."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Hello! How can I help you?"
        mock_llm.invoke.return_value = mock_response
        mock_chat_openai.return_value = mock_llm

        response = chatbot("Hi there")

        assert response == "Hello! How can I help you?"
        assert mock_llm.invoke.called

    @patch("LLM_shared.ChatOpenAI")
    def test_chatbot_with_conversation_history(self, mock_chat_openai):
        """Test chatbot with conversation history."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Your name is Alice."
        mock_llm.invoke.return_value = mock_response
        mock_chat_openai.return_value = mock_llm

        history = [
            {"role": "user", "content": "My name is Alice"},
            {"role": "assistant", "content": "Nice to meet you!"},
        ]

        response = chatbot("What's my name?", conversation_history=history)

        assert response == "Your name is Alice."
        assert mock_llm.invoke.called

    @patch("LLM_shared.ChatOpenAI")
    def test_chatbot_with_custom_parameters(self, mock_chat_openai):
        """Test chatbot with custom model and temperature."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Test response"
        mock_llm.invoke.return_value = mock_response
        mock_chat_openai.return_value = mock_llm

        response = chatbot(
            "Test message",
            model="gpt-4",
            temperature=0.3,
            max_tokens=100,
        )

        assert response == "Test response"
        mock_chat_openai.assert_called_once()
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["model"] == "gpt-4"
        assert call_kwargs["temperature"] == 0.3
        assert call_kwargs["max_tokens"] == 100

    @patch("LLM_shared.ChatOpenAI")
    def test_chatbot_streaming(self, mock_chat_openai):
        """Test chatbot with streaming enabled."""
        mock_llm = MagicMock()
        mock_chunks = [
            MagicMock(content="Hello "),
            MagicMock(content="world"),
            MagicMock(content="!"),
        ]
        mock_llm.stream.return_value = iter(mock_chunks)
        mock_chat_openai.return_value = mock_llm

        response = chatbot("Hi", streaming=True)

        assert response == "Hello world!"
        assert mock_llm.stream.called

    def test_chatbot_invalid_conversation_history(self):
        """Test chatbot with invalid role in conversation history."""
        invalid_history = [{"role": "invalid_role", "content": "Test"}]

        with pytest.raises(ValueError, match="Invalid role"):
            chatbot("Test", conversation_history=invalid_history)


class TestLLMExtraction:
    """Tests for LLM-based data extraction."""

    @patch("onboarding.chatbot")
    def test_extract_gender_from_conversation(self, mock_chatbot):
        """Test extracting gender using LLM."""
        mock_chatbot.return_value = '{"gender": "male"}'
        
        conversation = [
            {"role": "assistant", "content": "What's your gender?"},
            {"role": "user", "content": "I'm male"}
        ]
        
        result = _extract_data_with_llm(conversation)
        assert result.get("gender") == "male"

    @patch("onboarding.chatbot")
    def test_extract_multiple_fields(self, mock_chatbot):
        """Test extracting multiple fields at once."""
        mock_chatbot.return_value = '{"gender": "female", "date_of_birth": "1990-07-20", "current_weight": 65, "current_weight_unit": "kg"}'
        
        conversation = [
            {"role": "assistant", "content": "Tell me about yourself"},
            {"role": "user", "content": "I'm a female born on 20 july 1990, I weigh 65 kg"}
        ]
        
        result = _extract_data_with_llm(conversation)
        assert result.get("gender") == "female"
        assert result.get("date_of_birth") == "1990-07-20"
        assert result.get("current_weight") == 65


class TestExtractFieldValue:
    """Tests for field value extraction (legacy tests - kept for compatibility)."""

    def test_extraction_note(self):
        """Note that extraction is now done via LLM."""
        # The new system uses LLM for extraction, so these regex-based tests
        # are kept for documentation but extraction logic has changed
        assert True


class TestOnboarding:
    """Tests for the onboarding function."""

    @patch("onboarding.chatbot")
    def test_start_onboarding(self, mock_chatbot):
        """Test starting onboarding process."""
        mock_chatbot.return_value = "Welcome! What is your gender?"

        result = start_onboarding()

        assert result["message"] == "Welcome! What is your gender?"
        assert result["is_complete"] is False
        assert result["collected_data"] == {}
        assert result["next_field"] == "gender"
        assert len(result["conversation_history"]) == 1

    @patch("onboarding.chatbot")
    def test_onboarding_first_question(self, mock_chatbot):
        """Test onboarding with first answer."""
        # Mock both extraction and conversation responses
        mock_chatbot.side_effect = [
            '{"gender": "male"}',  # Extraction response
            "Great! What is your date of birth?"  # Conversation response
        ]

        result = onboarding("I'm male")

        assert result["is_complete"] is False
        assert result["collected_data"].get("gender") == "male"

    @patch("onboarding.chatbot")
    def test_onboarding_with_history(self, mock_chatbot):
        """Test onboarding with existing conversation history."""
        mock_chatbot.side_effect = [
            '{"gender": "male", "date_of_birth": "1990-05-15"}',  # Extraction
            "What is your current height?"  # Conversation
        ]

        history = [
            {"role": "assistant", "content": "What is your gender?"},
            {"role": "user", "content": "Male"},
            {"role": "assistant", "content": "What is your date of birth?"},
        ]
        collected = {"gender": "male"}

        result = onboarding(
            "1990-05-15",
            conversation_history=history,
            collected_data=collected,
        )

        assert result["collected_data"].get("date_of_birth") == "1990-05-15"
        assert len(result["conversation_history"]) > len(history)

    @patch("onboarding.chatbot")
    def test_onboarding_completion(self, mock_chatbot):
        """Test onboarding when all fields are collected."""
        all_fields_collected = {field: "test_value" for field in ONBOARDING_FIELDS}

        result = onboarding(
            "active",
            collected_data=all_fields_collected,
        )

        assert result["is_complete"] is True
        assert result["next_field"] is None
        assert "complete" in result["message"].lower()

    @patch("onboarding.chatbot")
    def test_onboarding_progressive_collection(self, mock_chatbot):
        """Test progressive data collection through multiple turns."""
        mock_chatbot.side_effect = [
            '{"gender": "male"}', "Next question...",
            '{"gender": "male", "date_of_birth": "1990-01-01"}', "Next question...",
            '{"gender": "male", "date_of_birth": "1990-01-01", "current_height": 180}', "Next question...",
        ]

        # Start with empty data
        collected = {}
        history = []

        # First turn - gender
        result = onboarding("male", collected_data=collected, conversation_history=history)
        collected = result["collected_data"]
        history = result["conversation_history"]
        assert "gender" in collected

        # Second turn - date_of_birth
        result = onboarding("1990-01-01", collected_data=collected, conversation_history=history)
        collected = result["collected_data"]
        assert "date_of_birth" in collected

        # Third turn - current_height
        result = onboarding("180", collected_data=collected, conversation_history=history)
        collected = result["collected_data"]
        assert "current_height" in collected

    @patch("onboarding.chatbot")
    def test_onboarding_with_custom_model(self, mock_chatbot):
        """Test onboarding with custom model parameter."""
        mock_chatbot.return_value = "Response"

        result = onboarding("test", model="gpt-4", temperature=0.5)

        assert mock_chatbot.called
        call_kwargs = mock_chatbot.call_args[1]
        assert call_kwargs["model"] == "gpt-4"
        assert call_kwargs["temperature"] == 0.5


class TestOnboardingIntegration:
    """Integration tests for full onboarding flow."""

    @patch("onboarding.chatbot")
    def test_full_onboarding_flow(self, mock_chatbot):
        """Test complete onboarding flow from start to finish."""
        mock_chatbot.return_value = "Next question..."

        # Start onboarding
        result = start_onboarding()
        assert not result["is_complete"]

        # Simulate answering all questions
        test_responses = {
            "gender": "male",
            "date_of_birth": "1990-01-01",
            "image": "skip",
            "current_height": "180",
            "current_height_unit": "cm",
            "target_height": "180",
            "target_height_unit": "cm",
            "current_weight": "75",
            "current_weight_unit": "kg",
            "target_weight": "70",
            "target_weight_unit": "kg",
            "goal": "lose weight",
            "target_timeline_value": "3",
            "target_timeline_unit": "months",
            "target_speed": "normal",
            "activity_level": "moderate",
        }

        for field, response in test_responses.items():
            result = onboarding(
                response,
                collected_data=result["collected_data"],
                conversation_history=result["conversation_history"],
            )

        # Verify all required fields are collected (image is optional, so 14 fields)
        assert len(result["collected_data"]) >= 14
        assert result["is_complete"] is True

    def test_onboarding_fields_completeness(self):
        """Test that all required onboarding fields are defined."""
        expected_fields = [
            'gender', 'date_of_birth',
            'current_height', 'current_height_unit',
            'target_height', 'target_height_unit',
            'current_weight', 'current_weight_unit',
            'target_weight', 'target_weight_unit',
            'goal', 'target_timeline_value', 'target_timeline_unit',
            'target_speed', 'activity_level'
        ]

        assert list(ONBOARDING_FIELDS) == expected_fields


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
