from typing import Optional, List, Dict
from langchain.tools import tool
from app.core.database import SessionLocal
from app.models.models import PantryItem, ShoppingItem, DailyMeal, MealPlan
from sqlalchemy import select

# We need a way to pass the user_id to these tools.
# Usually we'd bind them, or pass user_id as an argument.
# For simplicity, we will require user_id as an argument for now, 
# and the Agent wrapper will inject it.

@tool
def get_pantry_items(user_id: int) -> str:
    """Get a list of items in the user's pantry."""
    db = SessionLocal()
    try:
        items = db.execute(select(PantryItem).where(PantryItem.user_id == user_id)).scalars().all()
        if not items:
            return "Pantry is empty."
        return ", ".join([f"{item.item_name} ({item.quantity} {item.unit})" for item in items])
    finally:
        db.close()

@tool
def add_to_pantry(user_id: int, item_name: str, quantity: float, unit: str) -> str:
    """Add an item to the user's pantry."""
    db = SessionLocal()
    try:
        item = PantryItem(user_id=user_id, item_name=item_name, quantity=quantity, unit=unit, low_inventory_threshold=0)
        db.add(item)
        db.commit()
        return f"Added {quantity} {unit} of {item_name} to pantry."
    except Exception as e:
        return f"Error adding item: {e}"
    finally:
        db.close()

@tool
def get_shopping_list(user_id: int) -> str:
    """Get the current shopping list."""
    db = SessionLocal()
    try:
        items = db.execute(select(ShoppingItem).where(ShoppingItem.user_id == user_id)).scalars().all()
        if not items:
            return "Shopping list is empty."
        return ", ".join([f"{item.name}: {item.quantity} {item.unit}" for item in items])
    finally:
        db.close()

@tool
def log_meal(user_id: int, meal_description: str, meal_type: str) -> str:
    """Log a meal to the user's daily record. 
    Use this when the user says they ate something.
    meal_type should be 'breakfast', 'lunch', 'dinner', or 'snack'.
    """
    # In a real app, we'd use an LLM or nutrition API here to parse the description into nutrients.
    # For now, we'll just log the name.
    db = SessionLocal()
    try:
        # We need a meal plan to attach to? Or just daily meals?
        # The schema requires meal_plan_id. We might need to find the active meal plan.
        # For this prototype, we'll strip that requirement or fetch the active one.
        # START HACK: Find or create a dummy meal plan for today
        from datetime import date
        today = date.today()
        plan = db.execute(select(MealPlan).where(MealPlan.user_id == user_id, MealPlan.is_active == True)).scalars().first()
        if not plan:
             # Create a dummy plan if none exists (just to satisfy FK)
             plan = MealPlan(user_id=user_id, start_date=today, end_date=today, total_days=1)
             db.add(plan)
             db.commit()
             db.refresh(plan)
        
        meal = DailyMeal(
            user_id=user_id,
            meal_plan_id=plan.id,
            meal_date=today,
            meal_type=meal_type,
            name=meal_description,
            source="manual_log",
            tags={},
            nutrients={} # Placeholder
        )
        db.add(meal)
        db.commit()
        return f"Logged {meal_description} for {meal_type}."
    finally:
        db.close()

@tool
def generate_meal_suggestion(user_id: int, meal_type: str, goal: str = "maintain") -> str:
    """Generate a meal suggestion using AI.
    meal_type: breakfast, lunch, dinner, snack
    goal: lose_weight, maintain, gain_weight
    """
    from app.services.meal_generator import generate_meal
    
    # Mock user info for now since we might not have it all in DB yet
    # In reality, fetch from User table
    user_info = {
        "gender": "female", # Placeholder
        "date_of_birth": "1990-01-01",
        "current_height": 170, "current_height_unit": "cm",
        "current_weight": 70, "current_weight_unit": "kg",
        "target_weight": 65, "target_weight_unit": "kg",
        "goal": goal,
        "activity_level": "moderate"
    }
    
    try:
        meal = generate_meal(user_info, meal_type=meal_type)
        return f"Suggested {meal['name']}:\n{meal['meal_description']}\nCalories: {meal['nutrients']['calories']['value']}"
    except Exception as e:
        return f"Error generating meal: {e}"

@tool
def get_meal_history(user_id: int, days: int = 7) -> str:
    """Get the user's meal history for the last N days."""
    # Mock data for now as we don't have historical data generation
    return (
        "Last 7 days meal history:\n"
        "- Monday: Oatmeal (Breakfast), Salad (Lunch), Grilled Chicken (Dinner)\n"
        "- Tuesday: Eggs (Breakfast), Sandwich (Lunch), Pasta (Dinner)\n"
        "- Wednesday: Smoothie (Breakfast), Wrap (Lunch), Stir Fry (Dinner)\n"
        "Nutrient summary: Slightly low in protein, high in carbs."
    )

@tool
def get_saved_recipes(user_id: int) -> str:
    """Get the user's saved recipes."""
    # Mock data
    return (
        "Saved Recipes:\n"
        "1. Grandma's Lasagna (Cost: $15, High Carb)\n"
        "2. Quinoa Salad (Cost: $8, High Protein)\n"
        "3. Spicy Tacos (Cost: $12, Balanced)"
    )

@tool
def get_todays_meal_plan(user_id: int) -> str:
    """Get today's meal plan."""
    from datetime import date
    db = SessionLocal()
    try:
        today = date.today()
        # simplified fetch
        meals = db.execute(select(DailyMeal).where(DailyMeal.user_id == user_id, DailyMeal.meal_date == today)).scalars().all()
        if not meals:
            return "No meals planned for today."
        return "\n".join([f"{m.meal_type.capitalize()}: {m.name}" for m in meals])
    finally:
        db.close()

@tool
def update_user_profile(user_id: int, activity_level: Optional[str] = None, goal: Optional[str] = None, target_weight: Optional[float] = None, vegan: Optional[bool] = None, gluten_free: Optional[bool] = None, dairy_free: Optional[bool] = None, pescatarian: Optional[bool] = None) -> str:
    """Update user profile information.
    Use this to change activity_level (sedentary, light, moderate, active, very active), 
    goal (lose_weight, maintain, gain_weight), target_weight,
    or dietary preferences (vegan, gluten_free, dairy_free, pescatarian).
    """
    db = SessionLocal()
    try:
        from app.models.models import OnboardingProfile
        profile = db.execute(select(OnboardingProfile).where(OnboardingProfile.user_id == user_id)).scalars().first()
        if not profile:
            return "Profile not found."
            
        updates = []
        if activity_level:
            profile.activity_level = activity_level
            updates.append(f"activity level to '{activity_level}'")
        if goal:
            profile.goal = goal
            updates.append(f"goal to '{goal}'")
        if target_weight:
            profile.target_weight = target_weight
            updates.append(f"target weight to {target_weight}")
        
        # Boolean flags
        if vegan is not None:
            profile.vegan = vegan
            updates.append(f"vegan to {vegan}")
        if gluten_free is not None:
            profile.gluten_free = gluten_free
            updates.append(f"gluten_free to {gluten_free}")
        if dairy_free is not None:
            profile.dairy_free = dairy_free
            updates.append(f"dairy_free to {dairy_free}")
        if pescatarian is not None:
            profile.pescatarian = pescatarian
            updates.append(f"pescatarian to {pescatarian}")
            
        if not updates:
            return "No changes requested."
            
        db.commit()
        return f"Updated profile: {', '.join(updates)}."
    except Exception as e:
        return f"Error updating profile: {e}"
    finally:
        db.close()

ALL_TOOLS = [
    get_pantry_items, 
    add_to_pantry, 
    get_shopping_list, 
    log_meal, 
    generate_meal_suggestion,
    get_meal_history,
    get_saved_recipes,
    get_todays_meal_plan,
    update_user_profile
]
