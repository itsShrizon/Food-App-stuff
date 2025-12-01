"""Interactive meal generator demo script."""

import json
from meal_generator import generate_meal, generate_daily_meal_plan


def print_meal(meal: dict, meal_type: str):
    """Pretty print a meal with formatting."""
    print("\n" + "="*70)
    # Show meal name as title if available, otherwise use meal type
    meal_name = meal.get('meal_name', meal_type)
    print(f"🍽️  {meal_name.upper()} ({meal_type})")
    print("="*70)
    
    # Meal description
    if 'meal_description' in meal:
        print(f"\n📝 {meal['meal_description']}")
    
    # Ingredients
    print("\n📦 INGREDIENTS:")
    for ingredient in meal.get('ingredients', []):
        name = ingredient.get('name', 'Unknown')
        amount = ingredient.get('amount', 'N/A')
        print(f"   • {name}: {amount}")
    
    # Preparation time
    if 'preparation_time' in meal:
        print(f"\n⏱️  Preparation Time: {meal['preparation_time']}")
    
    # Cooking instructions
    if 'cooking_instructions' in meal:
        print(f"\n👨‍🍳 INSTRUCTIONS:")
        instructions = meal['cooking_instructions']
        # Wrap long text
        if len(instructions) > 65:
            words = instructions.split()
            lines = []
            current_line = "   "
            for word in words:
                if len(current_line) + len(word) + 1 <= 68:
                    current_line += word + " "
                else:
                    lines.append(current_line.rstrip())
                    current_line = "   " + word + " "
            lines.append(current_line.rstrip())
            print("\n".join(lines))
        else:
            print(f"   {instructions}")
    
    # Nutritional info
    if 'nutritional_info' in meal:
        print(f"\n📊 NUTRITIONAL INFO:")
        nutrition = meal['nutritional_info']
        print(f"   Calories: {nutrition.get('calories', 'N/A')}")
        print(f"   Protein: {nutrition.get('protein', 'N/A')}")
        print(f"   Carbs: {nutrition.get('carbohydrate', 'N/A')}")
        print(f"   Fat: {nutrition.get('fat', 'N/A')}")
    
    print("="*70)


def main():
    """Main function to run meal generator demo."""
    print("\n" + "="*70)
    print("🍽️  PERSONALIZED MEAL GENERATOR")
    print("="*70)
    print("\nThis tool generates personalized meals based on your fitness profile.")
    print("\nOptions:")
    print("  1. Generate a single meal (Breakfast/Lunch/Snacks/Dinner)")
    print("  2. Generate a complete daily meal plan")
    print("  3. Use sample profile (quick demo)")
    print("  4. Exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "4":
        print("\n👋 Goodbye!")
        return
    
    # Sample user profile for demo
    sample_user_info = {
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
    
    if choice == "3":
        print("\n" + "="*70)
        print("📋 Using Sample Profile:")
        print("="*70)
        print(json.dumps(sample_user_info, indent=2))
        user_info = sample_user_info
        
        # Ask if they want single meal or daily plan
        meal_choice = input("\nGenerate (1) Single meal or (2) Daily plan? (1/2): ").strip()
        choice = meal_choice
    else:
        # Custom profile input
        print("\n" + "="*70)
        print("📝 Enter Your Profile Information")
        print("="*70)
        
        try:
            gender = input("\nGender (male/female/others): ").strip().lower()
            dob = input("Date of Birth (YYYY-MM-DD): ").strip()
            height = input("Height in cm: ").strip()
            weight = input("Current Weight: ").strip()
            weight_unit = input("Weight unit (kg/lbs): ").strip().lower()
            target_weight = input("Target Weight: ").strip()
            target_weight_unit = input("Target weight unit (kg/lbs): ").strip().lower()
            
            print("\nFitness Goal:")
            print("  1. Lose weight")
            print("  2. Maintain weight")
            print("  3. Gain weight")
            goal_choice = input("Choose (1-3): ").strip()
            goal_map = {"1": "lose weight", "2": "maintain", "3": "gain weight"}
            goal = goal_map.get(goal_choice, "lose weight")
            
            print("\nActivity Level:")
            print("  1. Sedentary (little/no exercise)")
            print("  2. Light (exercise 1-3 days/week)")
            print("  3. Moderate (exercise 3-5 days/week)")
            print("  4. Active (exercise 6-7 days/week)")
            activity_choice = input("Choose (1-4): ").strip()
            activity_map = {"1": "sedentary", "2": "light", "3": "moderate", "4": "active"}
            activity_level = activity_map.get(activity_choice, "moderate")
            
            user_info = {
                "gender": gender,
                "date_of_birth": dob,
                "current_height": height,
                "current_weight": weight,
                "current_weight_unit": weight_unit,
                "target_weight": target_weight,
                "target_weight_unit": target_weight_unit,
                "goal": goal,
                "activity_level": activity_level
            }
        except KeyboardInterrupt:
            print("\n\n👋 Cancelled. Goodbye!")
            return
    
    # Generate meals based on choice
    if choice == "1":
        print("\n" + "="*70)
        print("Select Meal Type:")
        print("  1. Breakfast")
        print("  2. Snacks")
        print("  3. Lunch")
        print("  4. Dinner")
        meal_type_choice = input("\nChoose (1-4): ").strip()
        meal_type_map = {"1": "Breakfast", "2": "Snacks", "3": "Lunch", "4": "Dinner"}
        meal_type = meal_type_map.get(meal_type_choice, "Lunch")
        
        print(f"\n🤖 Generating {meal_type}...\n")
        
        try:
            meal = generate_meal(user_info, meal_type)
            print_meal(meal, meal_type)
            
            # Show raw JSON option
            show_json = input("\n\nShow raw JSON? (y/n): ").strip().lower()
            if show_json == 'y':
                print("\n" + "="*70)
                print("📄 RAW JSON:")
                print("="*70)
                print(json.dumps(meal, indent=2))
                print("="*70)
        
        except Exception as e:
            print(f"\n❌ Error generating meal: {e}")
            return
    
    elif choice == "2":
        print(f"\n🤖 Generating complete daily meal plan...\n")
        print("This may take a moment as we create 4 personalized meals...\n")
        
        try:
            meal_plan = generate_daily_meal_plan(user_info)
            
            print("\n" + "="*70)
            print("✅ DAILY MEAL PLAN GENERATED!")
            print("="*70)
            
            for meal_type, meal in meal_plan.items():
                print_meal(meal, meal_type)
                input("\nPress Enter to continue to next meal...")
            
            # Calculate total nutrition
            print("\n" + "="*70)
            print("📊 DAILY NUTRITIONAL SUMMARY")
            print("="*70)
            
            total_calories = 0
            total_protein = 0
            total_carbs = 0
            total_fat = 0
            
            for meal_type, meal in meal_plan.items():
                if 'nutritional_info' in meal:
                    nutrition = meal['nutritional_info']
                    # Extract numeric values (simple parsing)
                    try:
                        calories = nutrition.get('calories', '0kcal')
                        protein = nutrition.get('protein', '0g')
                        carbs = nutrition.get('carbohydrate', '0g')
                        fat = nutrition.get('fat', '0g')
                        
                        total_calories += int(''.join(filter(str.isdigit, calories)))
                        total_protein += int(''.join(filter(str.isdigit, protein)))
                        total_carbs += int(''.join(filter(str.isdigit, carbs)))
                        total_fat += int(''.join(filter(str.isdigit, fat)))
                    except:
                        pass
            
            print(f"\n   Total Daily Calories: {total_calories}kcal")
            print(f"   Total Protein: {total_protein}g")
            print(f"   Total Carbs: {total_carbs}g")
            print(f"   Total Fat: {total_fat}g")
            print("="*70)
            
            # Show raw JSON option
            show_json = input("\n\nShow raw JSON for all meals? (y/n): ").strip().lower()
            if show_json == 'y':
                print("\n" + "="*70)
                print("📄 COMPLETE MEAL PLAN (JSON):")
                print("="*70)
                print(json.dumps(meal_plan, indent=2))
                print("="*70)
        
        except Exception as e:
            print(f"\n❌ Error generating meal plan: {e}")
            return
    
    else:
        print("\n❌ Invalid choice. Please run the script again.")
        return
    
    print("\n✨ Thank you for using the Meal Generator!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
