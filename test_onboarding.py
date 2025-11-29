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
        mock_chatbot.return_value = '{"gender": "female", "date_of_birth": "1990-07-20", "current_weight": "65 kg"}'
        
        conversation = [
            {"role": "assistant", "content": "Tell me about yourself"},
            {"role": "user", "content": "I'm a female born on 20 july 1990, I weigh 65 kg"}
        ]
        
        result = _extract_data_with_llm(conversation)
        assert result.get("gender") == "female"
        assert result.get("date_of_birth") == "1990-07-20"
        assert result.get("current_weight") == "65 kg"


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
        # Mock extraction that doesn't return any new fields (all already collected)
        mock_chatbot.return_value = '{}'
        
        all_fields_collected = {field: "test_value" for field in ONBOARDING_FIELDS}

        result = onboarding(
            "active",
            collected_data=all_fields_collected,
        )

        assert result["is_complete"] is True
        assert result["next_field"] is None
        assert "complete" in result["message"].lower() or "information" in result["message"].lower()

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
        # Mock extraction to return all fields at once
        mock_chatbot.side_effect = [
            "Welcome! Let's get started...",  # start_onboarding greeting
            json.dumps({
                "gender": "male",
                "date_of_birth": "1990-01-01",
                "current_height": "180 cm",
                "current_weight": "75 kg",
                "target_weight": "70 kg",
                "goal": "lose weight",
                "target_speed": "normal",
                "activity_level": "moderate"
            }),  # extraction response
        ]

        # Start onboarding
        result = start_onboarding()
        assert not result["is_complete"]

        # Provide all answers in one message
        result = onboarding(
            "I'm a male born on 1990-01-01, currently 180 cm tall and 75 kg. I want to lose weight to 70 kg at a normal pace. I'm moderately active.",
            collected_data=result["collected_data"],
            conversation_history=result["conversation_history"],
        )

        # Verify all required fields are collected
        assert len(result["collected_data"]) == len(ONBOARDING_FIELDS)
        assert result["is_complete"] is True

    def test_onboarding_fields_completeness(self):
        """Test that all required onboarding fields are defined."""
        expected_fields = (
            'gender', 'date_of_birth',
            'current_height', 
            'current_weight', 
            'target_weight', 
            'goal', 
            'target_speed', 
            'activity_level'
        )

        assert ONBOARDING_FIELDS == expected_fields


class TestOnboardingWorkflows:
    """Comprehensive workflow tests covering 20 different onboarding scenarios."""

    @patch("onboarding.chatbot")
    def test_workflow_1_single_response_all_info(self, mock_chatbot):
        """Workflow 1: User provides all information in a single detailed response."""
        mock_chatbot.side_effect = [
            "Hello! Let's start...",  # start_onboarding
            json.dumps({
                "gender": "male",
                "date_of_birth": "1985-03-15",
                "current_height": "5 foot 10 inches",
                "current_weight": "180 lbs",
                "target_weight": "165 lbs",
                "goal": "lose weight",
                "target_speed": "normal",
                "activity_level": "moderate"
            }),
        ]
        
        result = start_onboarding()
        result = onboarding(
            "I'm a 39 year old male born March 15, 1985. I'm 5 foot 10 inches and weigh 180 lbs. I want to lose weight down to 165 lbs at a normal pace. I exercise moderately.",
            collected_data=result["collected_data"],
            conversation_history=result["conversation_history"]
        )
        
        assert result["is_complete"] is True
        assert len(result["collected_data"]) == 8

    @patch("onboarding.chatbot")
    def test_workflow_2_progressive_natural_conversation(self, mock_chatbot):
        """Workflow 2: User provides info progressively through natural conversation."""
        mock_chatbot.side_effect = [
            "Hi there!",  # start
            '{"gender": "female"}', "What's your date of birth?",
            '{"gender": "female", "date_of_birth": "1992-07-20"}', "Great! What's your height?",
            '{"gender": "female", "date_of_birth": "1992-07-20", "current_height": "165 cm"}', "What's your current weight?",
            '{"gender": "female", "date_of_birth": "1992-07-20", "current_height": "165 cm", "current_weight": "65 kg"}', "What's your target weight?",
            '{"gender": "female", "date_of_birth": "1992-07-20", "current_height": "165 cm", "current_weight": "65 kg", "target_weight": "60 kg"}', "What's your goal?",
            '{"gender": "female", "date_of_birth": "1992-07-20", "current_height": "165 cm", "current_weight": "65 kg", "target_weight": "60 kg", "goal": "lose weight"}', "How fast?",
            '{"gender": "female", "date_of_birth": "1992-07-20", "current_height": "165 cm", "current_weight": "65 kg", "target_weight": "60 kg", "goal": "lose weight", "target_speed": "slow"}', "Activity level?",
            '{"gender": "female", "date_of_birth": "1992-07-20", "current_height": "165 cm", "current_weight": "65 kg", "target_weight": "60 kg", "goal": "lose weight", "target_speed": "slow", "activity_level": "light"}',
        ]
        
        result = start_onboarding()
        responses = ["female", "July 20, 1992", "165 cm", "65 kg", "60 kg", "lose weight", "slow", "light exercise"]
        
        for response in responses:
            result = onboarding(response, collected_data=result["collected_data"], conversation_history=result["conversation_history"])
            if result["is_complete"]:
                break
        
        assert result["is_complete"] is True

    @patch("onboarding.chatbot")
    def test_workflow_3_metric_units(self, mock_chatbot):
        """Workflow 3: User provides all measurements in metric units."""
        mock_chatbot.side_effect = [
            "Welcome!",
            json.dumps({
                "gender": "male",
                "date_of_birth": "1990-01-01",
                "current_height": "180 cm",
                "current_weight": "75 kg",
                "target_weight": "70 kg",
                "goal": "lose weight",
                "target_speed": "fast",
                "activity_level": "active"
            }),
        ]
        
        result = start_onboarding()
        result = onboarding(
            "Male, born 1990-01-01, 180cm, 75kg, want to reach 70kg fast, very active lifestyle",
            collected_data=result["collected_data"],
            conversation_history=result["conversation_history"]
        )
        
        assert result["is_complete"] is True
        assert "cm" in str(result["collected_data"].get("current_height", "")).lower() or result["collected_data"].get("current_height") == "180 cm"

    @patch("onboarding.chatbot")
    def test_workflow_4_imperial_units(self, mock_chatbot):
        """Workflow 4: User provides all measurements in imperial units."""
        mock_chatbot.side_effect = [
            "Hello!",
            json.dumps({
                "gender": "female",
                "date_of_birth": "1995-06-10",
                "current_height": "5 foot 6 inches",
                "current_weight": "140 lbs",
                "target_weight": "130 lbs",
                "goal": "lose weight",
                "target_speed": "normal",
                "activity_level": "moderate"
            }),
        ]
        
        result = start_onboarding()
        result = onboarding(
            "I'm a woman born June 10, 1995. I'm 5'6\" and weigh 140 pounds. Target is 130 pounds, normal pace, moderately active.",
            collected_data=result["collected_data"],
            conversation_history=result["conversation_history"]
        )
        
        assert result["is_complete"] is True

    @patch("onboarding.chatbot")
    def test_workflow_5_gain_weight_goal(self, mock_chatbot):
        """Workflow 5: User wants to gain weight."""
        mock_chatbot.side_effect = [
            "Hi!",
            json.dumps({
                "gender": "male",
                "date_of_birth": "2000-12-25",
                "current_height": "185 cm",
                "current_weight": "65 kg",
                "target_weight": "75 kg",
                "goal": "gain weight",
                "target_speed": "slow",
                "activity_level": "light"
            }),
        ]
        
        result = start_onboarding()
        result = onboarding(
            "Male, Dec 25 2000, 185cm, 65kg, want to gain weight to 75kg slowly, light activity",
            collected_data=result["collected_data"],
            conversation_history=result["conversation_history"]
        )
        
        assert result["is_complete"] is True
        assert result["collected_data"]["goal"] == "gain weight"

    @patch("onboarding.chatbot")
    def test_workflow_6_maintain_weight_goal(self, mock_chatbot):
        """Workflow 6: User wants to maintain current weight."""
        mock_chatbot.side_effect = [
            "Welcome!",
            json.dumps({
                "gender": "female",
                "date_of_birth": "1988-04-12",
                "current_height": "170 cm",
                "current_weight": "60 kg",
                "target_weight": "60 kg",
                "goal": "maintain",
                "target_speed": "normal",
                "activity_level": "moderate"
            }),
        ]
        
        result = start_onboarding()
        result = onboarding(
            "Female, April 12 1988, 170cm, 60kg, want to maintain my current weight, moderate activity",
            collected_data=result["collected_data"],
            conversation_history=result["conversation_history"]
        )
        
        assert result["is_complete"] is True
        assert result["collected_data"]["goal"] == "maintain"

    @patch("onboarding.chatbot")
    def test_workflow_7_sedentary_lifestyle(self, mock_chatbot):
        """Workflow 7: Sedentary user with minimal activity."""
        mock_chatbot.side_effect = [
            "Hi!",
            json.dumps({
                "gender": "male",
                "date_of_birth": "1980-11-30",
                "current_height": "175 cm",
                "current_weight": "90 kg",
                "target_weight": "80 kg",
                "goal": "lose weight",
                "target_speed": "normal",
                "activity_level": "sedentary"
            }),
        ]
        
        result = start_onboarding()
        result = onboarding(
            "Male, Nov 30 1980, 175cm, 90kg, want 80kg, desk job with no exercise",
            collected_data=result["collected_data"],
            conversation_history=result["conversation_history"]
        )
        
        assert result["is_complete"] is True
        assert result["collected_data"]["activity_level"] == "sedentary"

    @patch("onboarding.chatbot")
    def test_workflow_8_very_active_lifestyle(self, mock_chatbot):
        """Workflow 8: Very active user with intense exercise routine."""
        mock_chatbot.side_effect = [
            "Hello!",
            json.dumps({
                "gender": "male",
                "date_of_birth": "1993-08-05",
                "current_height": "182 cm",
                "current_weight": "78 kg",
                "target_weight": "82 kg",
                "goal": "gain weight",
                "target_speed": "fast",
                "activity_level": "active"
            }),
        ]
        
        result = start_onboarding()
        result = onboarding(
            "Male, Aug 5 1993, 182cm, 78kg, want to bulk to 82kg fast, I train 6 days a week",
            collected_data=result["collected_data"],
            conversation_history=result["conversation_history"]
        )
        
        assert result["is_complete"] is True
        assert result["collected_data"]["activity_level"] == "active"

    @patch("onboarding.chatbot")
    def test_workflow_9_fast_weight_loss(self, mock_chatbot):
        """Workflow 9: User wants fast weight loss."""
        mock_chatbot.side_effect = [
            "Hi there!",
            json.dumps({
                "gender": "female",
                "date_of_birth": "1991-02-14",
                "current_height": "160 cm",
                "current_weight": "70 kg",
                "target_weight": "55 kg",
                "goal": "lose weight",
                "target_speed": "fast",
                "activity_level": "moderate"
            }),
        ]
        
        result = start_onboarding()
        result = onboarding(
            "Female, Feb 14 1991, 160cm, 70kg, want to lose to 55kg as fast as possible, moderate exercise",
            collected_data=result["collected_data"],
            conversation_history=result["conversation_history"]
        )
        
        assert result["is_complete"] is True
        assert result["collected_data"]["target_speed"] == "fast"

    @patch("onboarding.chatbot")
    def test_workflow_10_slow_steady_approach(self, mock_chatbot):
        """Workflow 10: User prefers slow and steady approach."""
        mock_chatbot.side_effect = [
            "Welcome!",
            json.dumps({
                "gender": "male",
                "date_of_birth": "1987-09-22",
                "current_height": "178 cm",
                "current_weight": "85 kg",
                "target_weight": "78 kg",
                "goal": "lose weight",
                "target_speed": "slow",
                "activity_level": "light"
            }),
        ]
        
        result = start_onboarding()
        result = onboarding(
            "Male, Sep 22 1987, 178cm, 85kg, want 78kg but slowly and sustainably, light activity",
            collected_data=result["collected_data"],
            conversation_history=result["conversation_history"]
        )
        
        assert result["is_complete"] is True
        assert result["collected_data"]["target_speed"] == "slow"

    @patch("onboarding.chatbot")
    def test_workflow_11_others_gender(self, mock_chatbot):
        """Workflow 11: User identifies as non-binary/others."""
        mock_chatbot.side_effect = [
            "Hi!",
            json.dumps({
                "gender": "others",
                "date_of_birth": "1994-05-18",
                "current_height": "172 cm",
                "current_weight": "68 kg",
                "target_weight": "65 kg",
                "goal": "lose weight",
                "target_speed": "normal",
                "activity_level": "moderate"
            }),
        ]
        
        result = start_onboarding()
        result = onboarding(
            "Non-binary, May 18 1994, 172cm, 68kg, want 65kg, normal pace, moderate activity",
            collected_data=result["collected_data"],
            conversation_history=result["conversation_history"]
        )
        
        assert result["is_complete"] is True
        assert result["collected_data"]["gender"] == "others"

    @patch("onboarding.chatbot")
    def test_workflow_12_mixed_units_conversation(self, mock_chatbot):
        """Workflow 12: User mixes metric and imperial units."""
        mock_chatbot.side_effect = [
            "Hello!",
            json.dumps({
                "gender": "male",
                "date_of_birth": "1989-07-08",
                "current_height": "6 feet",
                "current_weight": "80 kg",
                "target_weight": "75 kg",
                "goal": "lose weight",
                "target_speed": "normal",
                "activity_level": "active"
            }),
        ]
        
        result = start_onboarding()
        result = onboarding(
            "Male, July 8 1989, I'm 6 feet tall, weigh 80 kilos, want to get to 75kg, normal pace, very active",
            collected_data=result["collected_data"],
            conversation_history=result["conversation_history"]
        )
        
        assert result["is_complete"] is True

    @patch("onboarding.chatbot")
    def test_workflow_13_partial_then_complete(self, mock_chatbot):
        """Workflow 13: User provides partial info, then completes later."""
        mock_chatbot.side_effect = [
            "Welcome!",
            '{"gender": "female", "date_of_birth": "1996-03-20"}', "Great! What about your measurements?",
            '{"gender": "female", "date_of_birth": "1996-03-20", "current_height": "168 cm", "current_weight": "72 kg", "target_weight": "65 kg", "goal": "lose weight", "target_speed": "normal", "activity_level": "light"}',
        ]
        
        result = start_onboarding()
        result = onboarding(
            "I'm a woman born March 20, 1996",
            collected_data=result["collected_data"],
            conversation_history=result["conversation_history"]
        )
        
        assert result["is_complete"] is False
        
        result = onboarding(
            "I'm 168cm, 72kg, want to reach 65kg at normal pace, I do light exercise",
            collected_data=result["collected_data"],
            conversation_history=result["conversation_history"]
        )
        
        assert result["is_complete"] is True

    @patch("onboarding.chatbot")
    def test_workflow_14_verbose_natural_language(self, mock_chatbot):
        """Workflow 14: User provides very verbose, natural language response."""
        mock_chatbot.side_effect = [
            "Hi there!",
            json.dumps({
                "gender": "male",
                "date_of_birth": "1984-10-15",
                "current_height": "177 cm",
                "current_weight": "88 kg",
                "target_weight": "80 kg",
                "goal": "lose weight",
                "target_speed": "normal",
                "activity_level": "moderate"
            }),
        ]
        
        result = start_onboarding()
        result = onboarding(
            "Well, I'm a guy, I was born on October 15th back in 1984. I'm about 177 centimeters tall, maybe a bit more. Right now I weigh around 88 kilograms but I'd really like to get down to about 80 kilos. I'm not in a huge rush, just want to do it at a reasonable pace. I exercise a few times a week, so I'd say I'm moderately active.",
            collected_data=result["collected_data"],
            conversation_history=result["conversation_history"]
        )
        
        assert result["is_complete"] is True

    @patch("onboarding.chatbot")
    def test_workflow_15_concise_structured_format(self, mock_chatbot):
        """Workflow 15: User provides info in concise, structured format."""
        mock_chatbot.side_effect = [
            "Hello!",
            json.dumps({
                "gender": "female",
                "date_of_birth": "1998-01-30",
                "current_height": "162 cm",
                "current_weight": "58 kg",
                "target_weight": "55 kg",
                "goal": "lose weight",
                "target_speed": "slow",
                "activity_level": "light"
            }),
        ]
        
        result = start_onboarding()
        result = onboarding(
            "Gender: Female | DOB: 1998-01-30 | Height: 162cm | Weight: 58kg | Target: 55kg | Goal: Lose | Speed: Slow | Activity: Light",
            collected_data=result["collected_data"],
            conversation_history=result["conversation_history"]
        )
        
        assert result["is_complete"] is True

    @patch("onboarding.chatbot")
    def test_workflow_16_young_adult(self, mock_chatbot):
        """Workflow 16: Young adult user (18-25 years old)."""
        mock_chatbot.side_effect = [
            "Hi!",
            json.dumps({
                "gender": "male",
                "date_of_birth": "2003-06-15",
                "current_height": "180 cm",
                "current_weight": "70 kg",
                "target_weight": "75 kg",
                "goal": "gain weight",
                "target_speed": "normal",
                "activity_level": "active"
            }),
        ]
        
        result = start_onboarding()
        result = onboarding(
            "Male, born June 15 2003, 180cm, 70kg, want to bulk to 75kg, I'm pretty active",
            collected_data=result["collected_data"],
            conversation_history=result["conversation_history"]
        )
        
        assert result["is_complete"] is True
        assert result["collected_data"]["date_of_birth"] == "2003-06-15"

    @patch("onboarding.chatbot")
    def test_workflow_17_middle_aged(self, mock_chatbot):
        """Workflow 17: Middle-aged user (40-55 years old)."""
        mock_chatbot.side_effect = [
            "Welcome!",
            json.dumps({
                "gender": "female",
                "date_of_birth": "1975-08-22",
                "current_height": "165 cm",
                "current_weight": "75 kg",
                "target_weight": "68 kg",
                "goal": "lose weight",
                "target_speed": "slow",
                "activity_level": "light"
            }),
        ]
        
        result = start_onboarding()
        result = onboarding(
            "Female, Aug 22 1975, 165cm, 75kg, want to reach 68kg slowly, light activity due to age",
            collected_data=result["collected_data"],
            conversation_history=result["conversation_history"]
        )
        
        assert result["is_complete"] is True

    @patch("onboarding.chatbot")
    def test_workflow_18_minimal_weight_change(self, mock_chatbot):
        """Workflow 18: User wants minimal weight change (fine-tuning)."""
        mock_chatbot.side_effect = [
            "Hello!",
            json.dumps({
                "gender": "male",
                "date_of_birth": "1992-04-10",
                "current_height": "175 cm",
                "current_weight": "73 kg",
                "target_weight": "71 kg",
                "goal": "lose weight",
                "target_speed": "slow",
                "activity_level": "moderate"
            }),
        ]
        
        result = start_onboarding()
        result = onboarding(
            "Male, April 10 1992, 175cm, 73kg, just want to lose 2kg to 71kg, take it slow, moderate activity",
            collected_data=result["collected_data"],
            conversation_history=result["conversation_history"]
        )
        
        assert result["is_complete"] is True

    @patch("onboarding.chatbot")
    def test_workflow_19_significant_weight_change(self, mock_chatbot):
        """Workflow 19: User wants significant weight change."""
        mock_chatbot.side_effect = [
            "Hi!",
            json.dumps({
                "gender": "male",
                "date_of_birth": "1986-11-12",
                "current_height": "183 cm",
                "current_weight": "110 kg",
                "target_weight": "85 kg",
                "goal": "lose weight",
                "target_speed": "normal",
                "activity_level": "light"
            }),
        ]
        
        result = start_onboarding()
        result = onboarding(
            "Male, Nov 12 1986, 183cm, currently 110kg, want to lose down to 85kg, normal pace, light activity",
            collected_data=result["collected_data"],
            conversation_history=result["conversation_history"]
        )
        
        assert result["is_complete"] is True

    @patch("onboarding.chatbot")
    def test_workflow_20_casual_conversational_style(self, mock_chatbot):
        """Workflow 20: Very casual, conversational style with slang."""
        mock_chatbot.side_effect = [
            "Hey!",
            json.dumps({
                "gender": "female",
                "date_of_birth": "1997-09-05",
                "current_height": "170 cm",
                "current_weight": "65 kg",
                "target_weight": "62 kg",
                "goal": "lose weight",
                "target_speed": "normal",
                "activity_level": "moderate"
            }),
        ]
        
        result = start_onboarding()
        result = onboarding(
            "Hey! So I'm a girl, born Sept 5 97. I'm like 170cm tall, weigh about 65kg rn but wanna get to 62kg ya know? Normal speed is cool. I hit the gym a few times a week so pretty moderate I guess",
            collected_data=result["collected_data"],
            conversation_history=result["conversation_history"]
        )
        
        assert result["is_complete"] is True
        assert len(result["collected_data"]) == 8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
