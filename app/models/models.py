from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Text, JSON, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "accounts_user"

    id = Column(Integer, primary_key=True, index=True)
    password = Column(String(128), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(254), unique=True, nullable=False, index=True)
    phone = Column(String(15), unique=True, nullable=False)
    role = Column(String(8), nullable=False)
    device_token = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    is_staff = Column(Boolean, nullable=False, default=False)
    is_superuser = Column(Boolean, nullable=False, default=False)
    date_joined = Column(DateTime(timezone=True), nullable=False, default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    auth_provider = Column(String(20), nullable=False, default='email')

    # Relationships
    metabolic_profile = relationship("MetabolicProfile", back_populates="user", uselist=False)
    onboarding_profile = relationship("OnboardingProfile", back_populates="user", uselist=False)
    meal_plans = relationship("MealPlan", back_populates="user")
    pantry_items = relationship("PantryItem", back_populates="user")
    shopping_items = relationship("ShoppingItem", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")

class MetabolicProfile(Base):
    __tablename__ = "accounts_metabolicprofile"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts_user.id"), unique=True, nullable=False)
    bmr = Column(Numeric(10, 2))
    tdee = Column(Numeric(10, 2))
    daily_calorie_target = Column(Numeric(10, 2))
    protein_g = Column(Float)
    carbs_g = Column(Float)
    fats_g = Column(Float)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    user = relationship("User", back_populates="metabolic_profile")

class OnboardingProfile(Base):
    __tablename__ = "accounts_onboardingprofile"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts_user.id"), unique=True, nullable=False)
    gender = Column(String(10))
    date_of_birth = Column(Date)
    current_height = Column(Numeric(5, 2))
    current_height_unit = Column(String(5))
    current_weight = Column(Numeric(6, 2))
    current_weight_unit = Column(String(5))
    target_weight = Column(Numeric(6, 2))
    target_weight_unit = Column(String(5))
    goal = Column(String(15))
    activity_level = Column(String(20))
    vegan = Column(Boolean, default=False, nullable=False)
    dairy_free = Column(Boolean, default=False, nullable=False)
    gluten_free = Column(Boolean, default=False, nullable=False)
    pescatarian = Column(Boolean, default=False, nullable=False)
    last_message = Column(Text, nullable=False, default="")

    user = relationship("User", back_populates="onboarding_profile")

class MealPlan(Base):
    __tablename__ = "meals_mealplan"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts_user.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_days = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="meal_plans")
    daily_meals = relationship("DailyMeal", back_populates="meal_plan")

class DailyMeal(Base):
    __tablename__ = "meals_dailymeals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts_user.id"), nullable=False)
    meal_plan_id = Column(Integer, ForeignKey("meals_mealplan.id"), nullable=False)
    meal_date = Column(Date, nullable=False)
    meal_type = Column(String(20)) # breakfast, lunch, dinner, snack
    name = Column(String(255), nullable=False)
    source = Column(String(20), nullable=False) # generated, saved, manual
    nutrients = Column(JSON)
    tags = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    meal_plan = relationship("MealPlan", back_populates="daily_meals")
    food_items = relationship("FoodItem", back_populates="daily_meal")

class FoodItem(Base):
    __tablename__ = "meals_fooditem"

    id = Column(Integer, primary_key=True, index=True)
    meal_id = Column(Integer, ForeignKey("meals_dailymeals.id"), nullable=True)
    name = Column(String(255), nullable=False)
    quantity = Column(String(50))
    unit = Column(String(20))
    nutrients = Column(JSON)

    daily_meal = relationship("DailyMeal", back_populates="food_items")

class PantryItem(Base):
    __tablename__ = "pantry_pantryitem"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts_user.id"), nullable=False)
    item_name = Column(String(255), nullable=False)
    quantity = Column(Numeric(10, 2))
    unit = Column(String(50), nullable=False)
    low_inventory_threshold = Column(Float, nullable=False, default=0)
    expiration_date = Column(Date, nullable=True)
    nutrients = Column(JSON)
    last_updated = Column(DateTime(timezone=True), nullable=False, default=func.now())

    user = relationship("User", back_populates="pantry_items")

class ShoppingItem(Base):
    __tablename__ = "shopping_shoppingitem"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts_user.id"), nullable=False)
    name = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    bought = Column(Boolean, nullable=False, default=False)
    price = Column(Numeric(10, 2))
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    user = relationship("User", back_populates="shopping_items")

class ChatSession(Base):
    __tablename__ = "chats_chatsession"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts_user.id"), nullable=False)
    session = Column(String, unique=True, nullable=False) # UUID as string
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="chat_session")

class ChatMessage(Base):
    __tablename__ = "chats_chatmessage"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chats_chatsession.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("accounts_user.id"), nullable=True)
    role = Column(String(20), nullable=False) # user, assistant, system
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    chat_session = relationship("ChatSession", back_populates="messages")
