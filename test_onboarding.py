"""Test suite for LLM_shared and onboarding modules."""

import json
from unittest.mock import MagicMock, patch

import pytest

from LLM_shared import chatbot
from onboarding import (
    ONBOARDING_FIELDS,
    _extract_field_value,
    onboarding,
    start_onboarding,
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


class TestExtractFieldValue:
    """Tests for field value extraction."""

    def test_extract_gender_male(self):
        """Test extracting male gender."""
        assert _extract_field_value("I'm male", "gender", {}) == "male"
        assert _extract_field_value("I am a man", "gender", {}) == "male"

    def test_extract_gender_female(self):
        """Test extracting female gender."""
        assert _extract_field_value("I'm female", "gender", {}) == "female"
        assert _extract_field_value("I am a woman", "gender", {}) == "female"

    def test_extract_gender_others(self):
        """Test extracting other gender."""
        assert _extract_field_value("I prefer not to say", "gender", {}) == "others"
        assert _extract_field_value("Other", "gender", {}) == "others"

    def test_extract_date_of_birth(self):
        """Test extracting date of birth."""
        assert _extract_field_value("1990-05-15", "date_of_birth", {}) == "1990-05-15"
        assert _extract_field_value("My birthday is 05/15/1990", "date_of_birth", {}) == "05/15/1990"

    def test_extract_height(self):
        """Test extracting height values."""
        assert _extract_field_value("175", "current_height", {}) == 175.0
        assert _extract_field_value("5.8 feet", "current_height", {}) == 5.8

    def test_extract_height_unit(self):
        """Test extracting height units."""
        assert _extract_field_value("cm", "current_height_unit", {}) == "cm"
        assert _extract_field_value("inches", "current_height_unit", {}) == "inch"

    def test_extract_weight(self):
        """Test extracting weight values."""
        assert _extract_field_value("75", "current_weight", {}) == 75.0
        assert _extract_field_value("I weigh 65.5", "current_weight", {}) == 65.5

    def test_extract_weight_unit(self):
        """Test extracting weight units."""
        assert _extract_field_value("kg", "current_weight_unit", {}) == "kg"
        assert _extract_field_value("pounds", "current_weight_unit", {}) == "lbs"

    def test_extract_goal(self):
        """Test extracting fitness goals."""
        assert _extract_field_value("I want to lose weight", "goal", {}) == "lose_weight"
        assert _extract_field_value("maintain my weight", "goal", {}) == "maintain"
        assert _extract_field_value("gain weight", "goal", {}) == "gain_weight"

    def test_extract_timeline_value(self):
        """Test extracting timeline values."""
        assert _extract_field_value("30", "target_timeline_value", {}) == 30
        assert _extract_field_value("In 6 months", "target_timeline_value", {}) == 6

    def test_extract_timeline_unit(self):
        """Test extracting timeline units."""
        assert _extract_field_value("days", "target_timeline_unit", {}) == "days"
        assert _extract_field_value("in 3 weeks", "target_timeline_unit", {}) == "weeks"
        assert _extract_field_value("months", "target_timeline_unit", {}) == "months"

    def test_extract_target_speed(self):
        """Test extracting target speed."""
        assert _extract_field_value("slow", "target_speed", {}) == "slow"
        assert _extract_field_value("normal pace", "target_speed", {}) == "normal"
        assert _extract_field_value("fast", "target_speed", {}) == "fast"

    def test_extract_activity_level(self):
        """Test extracting activity level."""
        assert _extract_field_value("sedentary", "activity_level", {}) == "sedentary"
        assert _extract_field_value("light exercise", "activity_level", {}) == "light"
        assert _extract_field_value("moderate", "activity_level", {}) == "moderate"
        assert _extract_field_value("very active", "activity_level", {}) == "active"

    def test_extract_image_skip(self):
        """Test skipping image upload."""
        assert _extract_field_value("skip", "image", {}) == "users/avatar.png"
        assert _extract_field_value("no thanks", "image", {}) == "users/avatar.png"

    def test_extract_invalid_field(self):
        """Test extracting from invalid field returns None."""
        assert _extract_field_value("test", "invalid_field", {}) is None


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
        mock_chatbot.return_value = "Great! What is your date of birth?"

        result = onboarding("I'm male")

        assert result["is_complete"] is False
        assert result["collected_data"]["gender"] == "male"
        assert result["next_field"] == "date_of_birth"

    @patch("onboarding.chatbot")
    def test_onboarding_with_history(self, mock_chatbot):
        """Test onboarding with existing conversation history."""
        mock_chatbot.return_value = "What is your current height?"

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

        assert result["collected_data"]["date_of_birth"] == "1990-05-15"
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
        mock_chatbot.return_value = "Next question..."

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

        # Third turn - skip image
        result = onboarding("skip", collected_data=collected, conversation_history=history)
        collected = result["collected_data"]
        assert "image" in collected

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

        # Verify all fields are collected
        assert len(result["collected_data"]) == len(ONBOARDING_FIELDS)
        assert result["is_complete"] is True

    def test_onboarding_fields_completeness(self):
        """Test that all required onboarding fields are defined."""
        expected_fields = [
            'gender', 'date_of_birth', 'image',
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
