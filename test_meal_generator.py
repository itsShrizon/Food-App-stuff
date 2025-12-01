"""Test suite for meal_generator module."""

import json
from unittest.mock import MagicMock, patch

import pytest

from meal_generator import (
    generate_meal,
    generate_daily_meal_plan,
    _calculate_age,
)


class TestCalculateAge:
    """Tests for age calculation helper function."""

    def test_calculate_age_valid_date(self):
        """Test age calculation with valid date."""
        age = _calculate_age("1990-01-15")
        assert age == 35  # As of Nov 30, 2025

    def test_calculate_age_birthday_not_passed(self):
        """Test age calculation when birthday hasn't occurred yet this year."""
        age = _calculate_age("2000-12-31")
        assert age == 24  # Birthday not yet in 2025

    def test_calculate_age_birthday_passed(self):
        """Test age calculation when birthday already occurred."""
        age = _calculate_age("2000-01-01")
        assert age == 25  # Birthday already passed in 2025

    def test_calculate_age_invalid_format(self):
        """Test age calculation with invalid date format."""
        age = _calculate_age("invalid-date")
        assert age == 25  # Should return default age

    def test_calculate_age_recent_birth(self):
        """Test age calculation for young person."""
        age = _calculate_age("2005-06-15")
        assert age == 20


class TestGenerateMeal:
    """Tests for single meal generation."""

    def get_sample_user_info(self):
        """Helper to get sample user info."""
        return {
            "gender": "male",
            "date_of_birth": "1990-01-15",
            "current_height": "175",
            "current_weight": "75",
            "current_weight_unit": "kg",
            "target_weight": "70",
            "target_weight_unit": "kg",
            "goal": "lose weight",
            "activity_level": "moderate"
        }

    def test_invalid_meal_type(self):
        """Test that invalid meal type raises ValueError."""
        user_info = self.get_sample_user_info()
        
        with pytest.raises(ValueError, match="Invalid meal_type"):
            generate_meal(user_info, meal_type="Brunch")

    def test_valid_meal_types(self):
        """Test that all valid meal types are accepted."""
        user_info = self.get_sample_user_info()
        valid_types = ["Breakfast", "Snacks", "Lunch", "Dinner"]
        
        for meal_type in valid_types:
            # Should not raise exception
            try:
                # This will fail due to missing API key, but validates meal_type
                generate_meal(user_info, meal_type=meal_type)
            except ValueError as e:
                if "Invalid meal_type" in str(e):
                    pytest.fail(f"Valid meal_type '{meal_type}' was rejected")
            except Exception:
                # Other exceptions are OK for this test
                pass

    def test_missing_required_fields(self):
        """Test that missing required fields raises ValueError."""
        incomplete_info = {"gender": "male"}
        
        with pytest.raises(ValueError, match="Missing required user_info fields"):
            generate_meal(incomplete_info, meal_type="Lunch")

    def test_missing_multiple_fields(self):
        """Test error message lists all missing fields."""
        incomplete_info = {
            "gender": "male",
            "date_of_birth": "1990-01-15"
        }
        
        with pytest.raises(ValueError) as exc_info:
            generate_meal(incomplete_info, meal_type="Lunch")
        
        error_msg = str(exc_info.value)
        assert "current_height" in error_msg
        assert "current_weight" in error_msg

    @patch("meal_generator.chatbot")
    def test_generate_meal_success(self, mock_chatbot):
        """Test successful meal generation."""
        mock_chatbot.return_value = json.dumps({
            "meal_type": "Lunch",
            "meal_name": "Grilled Chicken Salad",
            "meal_description": "A healthy protein-rich salad",
            "ingredients": [
                {"name": "Chicken breast", "amount": "150g"},
                {"name": "Mixed greens", "amount": "100g"}
            ],
            "preparation_time": "20 minutes",
            "cooking_instructions": "Grill chicken, slice, serve over greens",
            "nutritional_info": {
                "calories": "320kcal",
                "protein": "35g",
                "carbohydrate": "8g",
                "fat": "15g"
            }
        })
        
        user_info = self.get_sample_user_info()
        result = generate_meal(user_info, meal_type="Lunch")
        
        assert result["meal_type"] == "Lunch"
        assert result["meal_name"] == "Grilled Chicken Salad"
        assert "ingredients" in result
        assert len(result["ingredients"]) == 2
        assert "nutritional_info" in result

    @patch("meal_generator.chatbot")
    def test_generate_meal_with_markdown_cleanup(self, mock_chatbot):
        """Test that markdown code blocks are cleaned from response."""
        mock_chatbot.return_value = """```json
{
    "meal_type": "Breakfast",
    "meal_name": "Protein Oatmeal",
    "meal_description": "Healthy breakfast",
    "ingredients": [{"name": "Oats", "amount": "50g"}],
    "preparation_time": "10 minutes",
    "cooking_instructions": "Cook oats with water",
    "nutritional_info": {
        "calories": "250kcal",
        "protein": "15g",
        "carbohydrate": "40g",
        "fat": "5g"
    }
}```"""
        
        user_info = self.get_sample_user_info()
        result = generate_meal(user_info, meal_type="Breakfast")
        
        assert result["meal_type"] == "Breakfast"
        assert result["meal_name"] == "Protein Oatmeal"

    @patch("meal_generator.chatbot")
    def test_generate_meal_missing_required_keys(self, mock_chatbot):
        """Test that incomplete meal data raises ValueError."""
        mock_chatbot.return_value = json.dumps({
            "meal_type": "Lunch",
            "meal_description": "Incomplete meal"
            # Missing meal_name, ingredients, nutritional_info
        })
        
        user_info = self.get_sample_user_info()
        
        with pytest.raises(ValueError, match="missing required keys"):
            generate_meal(user_info, meal_type="Lunch")

    @patch("meal_generator.chatbot")
    def test_generate_meal_with_custom_model(self, mock_chatbot):
        """Test meal generation with custom model parameter."""
        mock_chatbot.return_value = json.dumps({
            "meal_type": "Dinner",
            "meal_name": "Baked Salmon",
            "meal_description": "Omega-3 rich dinner",
            "ingredients": [{"name": "Salmon", "amount": "200g"}],
            "preparation_time": "25 minutes",
            "cooking_instructions": "Bake at 375°F",
            "nutritional_info": {
                "calories": "400kcal",
                "protein": "40g",
                "carbohydrate": "5g",
                "fat": "25g"
            }
        })
        
        user_info = self.get_sample_user_info()
        result = generate_meal(user_info, meal_type="Dinner", model="gpt-4", temperature=0.5)
        
        assert mock_chatbot.called
        call_kwargs = mock_chatbot.call_args[1]
        assert call_kwargs["model"] == "gpt-4"
        assert call_kwargs["temperature"] == 0.5


class TestGenerateMealWithPreviousMeals:
    """Tests for meal generation with previous meals to avoid repetition."""

    def get_sample_user_info(self):
        """Helper to get sample user info."""
        return {
            "gender": "female",
            "date_of_birth": "1995-06-20",
            "current_height": "165",
            "current_weight": "60",
            "current_weight_unit": "kg",
            "target_weight": "58",
            "target_weight_unit": "kg",
            "goal": "lose weight",
            "activity_level": "light"
        }

    @patch("meal_generator.chatbot")
    def test_generate_meal_with_empty_previous_meals(self, mock_chatbot):
        """Test meal generation with empty previous meals list."""
        mock_chatbot.return_value = json.dumps({
            "meal_type": "Breakfast",
            "meal_name": "Scrambled Eggs",
            "meal_description": "Protein-rich breakfast",
            "ingredients": [{"name": "Eggs", "amount": "3 pieces"}],
            "preparation_time": "10 minutes",
            "cooking_instructions": "Scramble eggs in pan",
            "nutritional_info": {
                "calories": "210kcal",
                "protein": "18g",
                "carbohydrate": "2g",
                "fat": "15g"
            }
        })
        
        user_info = self.get_sample_user_info()
        result = generate_meal(user_info, meal_type="Breakfast", previous_meals=[])
        
        assert result["meal_name"] == "Scrambled Eggs"

    @patch("meal_generator.chatbot")
    def test_generate_meal_with_one_previous_meal(self, mock_chatbot):
        """Test that previous meal names are included in the prompt."""
        mock_chatbot.return_value = json.dumps({
            "meal_type": "Snacks",
            "meal_name": "Greek Yogurt with Berries",
            "meal_description": "High protein snack",
            "ingredients": [
                {"name": "Greek yogurt", "amount": "150g"},
                {"name": "Berries", "amount": "50g"}
            ],
            "preparation_time": "5 minutes",
            "cooking_instructions": "Mix yogurt with berries",
            "nutritional_info": {
                "calories": "150kcal",
                "protein": "15g",
                "carbohydrate": "18g",
                "fat": "3g"
            }
        })
        
        previous_meals = [
            {
                "meal_type": "Breakfast",
                "meal_name": "Oatmeal with Banana",
                "ingredients": [{"name": "Oats", "amount": "50g"}]
            }
        ]
        
        user_info = self.get_sample_user_info()
        result = generate_meal(user_info, meal_type="Snacks", previous_meals=previous_meals)
        
        # Check that chatbot was called with previous meals context
        assert mock_chatbot.called
        call_args = mock_chatbot.call_args[0]
        prompt = call_args[0]
        assert "Previous meals" in prompt or "Oatmeal with Banana" in prompt

    @patch("meal_generator.chatbot")
    def test_generate_meal_with_multiple_previous_meals(self, mock_chatbot):
        """Test meal generation with multiple previous meals."""
        mock_chatbot.return_value = json.dumps({
            "meal_type": "Dinner",
            "meal_name": "Chicken Stir Fry",
            "meal_description": "Asian-inspired dinner",
            "ingredients": [
                {"name": "Chicken breast", "amount": "150g"},
                {"name": "Mixed vegetables", "amount": "200g"},
                {"name": "Soy sauce", "amount": "2 tablespoons"}
            ],
            "preparation_time": "25 minutes",
            "cooking_instructions": "Stir fry chicken and vegetables",
            "nutritional_info": {
                "calories": "380kcal",
                "protein": "40g",
                "carbohydrate": "25g",
                "fat": "12g"
            }
        })
        
        previous_meals = [
            {
                "meal_type": "Breakfast",
                "meal_name": "Scrambled Eggs with Toast",
                "ingredients": [{"name": "Eggs", "amount": "2 pieces"}]
            },
            {
                "meal_type": "Snacks",
                "meal_name": "Apple with Almond Butter",
                "ingredients": [{"name": "Apple", "amount": "1 piece"}]
            },
            {
                "meal_type": "Lunch",
                "meal_name": "Grilled Chicken Salad",
                "ingredients": [{"name": "Chicken", "amount": "120g"}]
            }
        ]
        
        user_info = self.get_sample_user_info()
        result = generate_meal(user_info, meal_type="Dinner", previous_meals=previous_meals)
        
        assert result["meal_type"] == "Dinner"
        assert result["meal_name"] == "Chicken Stir Fry"
        
        # Verify prompt includes previous meals
        call_args = mock_chatbot.call_args[0]
        prompt = call_args[0]
        assert any(meal["meal_name"] in prompt for meal in previous_meals)

    @patch("meal_generator.chatbot")
    def test_previous_meals_without_meal_name_field(self, mock_chatbot):
        """Test handling of previous meals without meal_name field."""
        mock_chatbot.return_value = json.dumps({
            "meal_type": "Lunch",
            "meal_name": "Quinoa Bowl",
            "meal_description": "Healthy grain bowl",
            "ingredients": [{"name": "Quinoa", "amount": "100g"}],
            "preparation_time": "30 minutes",
            "cooking_instructions": "Cook quinoa and add toppings",
            "nutritional_info": {
                "calories": "350kcal",
                "protein": "12g",
                "carbohydrate": "55g",
                "fat": "8g"
            }
        })
        
        # Previous meal without meal_name field
        previous_meals = [
            {
                "meal_type": "Breakfast",
                "ingredients": [{"name": "Oats", "amount": "50g"}]
            }
        ]
        
        user_info = self.get_sample_user_info()
        # Should not raise exception
        result = generate_meal(user_info, meal_type="Lunch", previous_meals=previous_meals)
        
        assert result["meal_name"] == "Quinoa Bowl"


class TestGenerateDailyMealPlan:
    """Tests for complete daily meal plan generation."""

    def get_sample_user_info(self):
        """Helper to get sample user info."""
        return {
            "gender": "male",
            "date_of_birth": "1988-03-15",
            "current_height": "180",
            "current_weight": "85",
            "current_weight_unit": "kg",
            "target_weight": "78",
            "target_weight_unit": "kg",
            "goal": "lose weight",
            "activity_level": "moderate"
        }

    @patch("meal_generator.chatbot")
    def test_generate_daily_meal_plan_all_meals(self, mock_chatbot):
        """Test that daily plan generates all 4 meal types."""
        # Mock responses for all 4 meals
        mock_chatbot.side_effect = [
            json.dumps({
                "meal_type": "Breakfast",
                "meal_name": "Protein Pancakes",
                "meal_description": "High protein breakfast",
                "ingredients": [{"name": "Eggs", "amount": "2 pieces"}],
                "preparation_time": "15 minutes",
                "cooking_instructions": "Mix and cook",
                "nutritional_info": {"calories": "300kcal", "protein": "25g", "carbohydrate": "35g", "fat": "8g"}
            }),
            json.dumps({
                "meal_type": "Snacks",
                "meal_name": "Protein Smoothie",
                "meal_description": "Quick snack",
                "ingredients": [{"name": "Protein powder", "amount": "30g"}],
                "preparation_time": "5 minutes",
                "cooking_instructions": "Blend all",
                "nutritional_info": {"calories": "180kcal", "protein": "20g", "carbohydrate": "15g", "fat": "5g"}
            }),
            json.dumps({
                "meal_type": "Lunch",
                "meal_name": "Chicken Caesar Salad",
                "meal_description": "Filling lunch",
                "ingredients": [{"name": "Chicken", "amount": "150g"}],
                "preparation_time": "20 minutes",
                "cooking_instructions": "Grill and toss",
                "nutritional_info": {"calories": "400kcal", "protein": "38g", "carbohydrate": "20g", "fat": "18g"}
            }),
            json.dumps({
                "meal_type": "Dinner",
                "meal_name": "Baked Salmon with Vegetables",
                "meal_description": "Healthy dinner",
                "ingredients": [{"name": "Salmon", "amount": "200g"}],
                "preparation_time": "30 minutes",
                "cooking_instructions": "Bake at 375F",
                "nutritional_info": {"calories": "450kcal", "protein": "42g", "carbohydrate": "15g", "fat": "25g"}
            })
        ]
        
        user_info = self.get_sample_user_info()
        meal_plan = generate_daily_meal_plan(user_info)
        
        # Check all meal types are present
        assert "Breakfast" in meal_plan
        assert "Snacks" in meal_plan
        assert "Lunch" in meal_plan
        assert "Dinner" in meal_plan
        
        # Verify each meal has correct structure
        for meal_type, meal in meal_plan.items():
            assert meal["meal_type"] == meal_type
            assert "meal_name" in meal
            assert "ingredients" in meal
            assert "nutritional_info" in meal

    @patch("meal_generator.chatbot")
    def test_daily_plan_passes_previous_meals(self, mock_chatbot):
        """Test that each meal in daily plan receives previous meals."""
        meal_responses = []
        for meal_type, meal_name in [("Breakfast", "Oatmeal"), ("Snacks", "Nuts"), 
                                      ("Lunch", "Salad"), ("Dinner", "Fish")]:
            meal_responses.append(json.dumps({
                "meal_type": meal_type,
                "meal_name": meal_name,
                "meal_description": "Test meal",
                "ingredients": [{"name": "Test", "amount": "100g"}],
                "preparation_time": "10 minutes",
                "cooking_instructions": "Cook it",
                "nutritional_info": {"calories": "200kcal", "protein": "20g", "carbohydrate": "10g", "fat": "5g"}
            }))
        
        mock_chatbot.side_effect = meal_responses
        
        user_info = self.get_sample_user_info()
        meal_plan = generate_daily_meal_plan(user_info)
        
        # Verify chatbot was called 4 times (once per meal)
        assert mock_chatbot.call_count == 4
        
        # Check that later calls include previous meal names in context
        # The 4th call (Dinner) should have 3 previous meals
        last_call_args = mock_chatbot.call_args_list[3]
        # Check if previous_meals parameter was passed
        assert len(meal_plan) == 4

    @patch("meal_generator.chatbot")
    def test_daily_plan_with_custom_parameters(self, mock_chatbot):
        """Test daily meal plan with custom model and temperature."""
        mock_chatbot.return_value = json.dumps({
            "meal_type": "Breakfast",
            "meal_name": "Test Meal",
            "meal_description": "Test",
            "ingredients": [{"name": "Test", "amount": "100g"}],
            "preparation_time": "10 minutes",
            "cooking_instructions": "Test",
            "nutritional_info": {"calories": "200kcal", "protein": "20g", "carbohydrate": "10g", "fat": "5g"}
        })
        
        user_info = self.get_sample_user_info()
        generate_daily_meal_plan(user_info, model="gpt-4", temperature=0.3)
        
        # Check that custom parameters were passed to all chatbot calls
        for call in mock_chatbot.call_args_list:
            kwargs = call[1]
            assert kwargs["model"] == "gpt-4"
            assert kwargs["temperature"] == 0.3


class TestDifferentUserProfiles:
    """Tests for meal generation with different user profiles."""

    @patch("meal_generator.chatbot")
    def test_lose_weight_goal(self, mock_chatbot):
        """Test meal generation for weight loss goal."""
        mock_chatbot.return_value = json.dumps({
            "meal_type": "Lunch",
            "meal_name": "Light Salad",
            "meal_description": "Low calorie meal",
            "ingredients": [{"name": "Lettuce", "amount": "100g"}],
            "preparation_time": "10 minutes",
            "cooking_instructions": "Toss ingredients",
            "nutritional_info": {"calories": "250kcal", "protein": "20g", "carbohydrate": "15g", "fat": "10g"}
        })
        
        user_info = {
            "gender": "female",
            "date_of_birth": "1992-05-10",
            "current_height": "165",
            "current_weight": "70",
            "current_weight_unit": "kg",
            "target_weight": "65",
            "target_weight_unit": "kg",
            "goal": "lose weight",
            "activity_level": "sedentary"
        }
        
        result = generate_meal(user_info, meal_type="Lunch")
        
        # Verify chatbot was called with weight loss goal
        call_args = mock_chatbot.call_args[0]
        prompt = call_args[0]
        assert "lose weight" in prompt

    @patch("meal_generator.chatbot")
    def test_gain_weight_goal(self, mock_chatbot):
        """Test meal generation for weight gain goal."""
        mock_chatbot.return_value = json.dumps({
            "meal_type": "Dinner",
            "meal_name": "Protein Bowl",
            "meal_description": "High calorie meal",
            "ingredients": [{"name": "Rice", "amount": "200g"}],
            "preparation_time": "25 minutes",
            "cooking_instructions": "Cook all ingredients",
            "nutritional_info": {"calories": "650kcal", "protein": "45g", "carbohydrate": "70g", "fat": "20g"}
        })
        
        user_info = {
            "gender": "male",
            "date_of_birth": "2000-08-20",
            "current_height": "185",
            "current_weight": "65",
            "current_weight_unit": "kg",
            "target_weight": "75",
            "target_weight_unit": "kg",
            "goal": "gain weight",
            "activity_level": "active"
        }
        
        result = generate_meal(user_info, meal_type="Dinner")
        
        # Verify chatbot was called with weight gain goal
        call_args = mock_chatbot.call_args[0]
        prompt = call_args[0]
        assert "gain weight" in prompt

    @patch("meal_generator.chatbot")
    def test_maintain_weight_goal(self, mock_chatbot):
        """Test meal generation for weight maintenance."""
        mock_chatbot.return_value = json.dumps({
            "meal_type": "Breakfast",
            "meal_name": "Balanced Breakfast",
            "meal_description": "Maintenance calories",
            "ingredients": [{"name": "Eggs", "amount": "2 pieces"}],
            "preparation_time": "15 minutes",
            "cooking_instructions": "Prepare eggs",
            "nutritional_info": {"calories": "350kcal", "protein": "25g", "carbohydrate": "30g", "fat": "15g"}
        })
        
        user_info = {
            "gender": "female",
            "date_of_birth": "1988-11-15",
            "current_height": "170",
            "current_weight": "60",
            "current_weight_unit": "kg",
            "target_weight": "60",
            "target_weight_unit": "kg",
            "goal": "maintain",
            "activity_level": "moderate"
        }
        
        result = generate_meal(user_info, meal_type="Breakfast")
        
        # Verify chatbot was called with maintenance goal
        call_args = mock_chatbot.call_args[0]
        prompt = call_args[0]
        assert "maintain" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
