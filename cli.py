
import asyncio
import os
import sys
from sqlalchemy import select
from app.services.agent_service import agent_service
from app.core.database import SessionLocal
from datetime import datetime
from app.models.models import User, OnboardingProfile

# Ensure we can import app modules
sys.path.append(os.getcwd())

async def get_or_create_user(db):
    """Ensure a test user exists."""
    user = db.execute(select(User).where(User.email == "test@example.com")).scalars().first()
    if not user:
        print("Creating test user (ID 1)...")
        user = User(
            email="test@example.com",
            password="dummy_password",
            name="Test User",
            phone="1234567890",
            role="user"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Ensure onboarding profile exists so the agent knows something
    # Ensure onboarding profile exists so the agent knows something
    profile = db.execute(select(OnboardingProfile).where(OnboardingProfile.user_id == user.id)).scalars().first()
    if not profile:
        print("Creating default onboarding profile...")
        profile = OnboardingProfile(
            user_id=user.id,
            gender="male",
            date_of_birth=datetime.strptime("1990-01-01", "%Y-%m-%d").date(),
            current_height=180,
            current_height_unit="cm",
            current_weight=75,
            current_weight_unit="kg",
            target_weight=70,
            target_weight_unit="kg",
            goal="lose_weight",
            activity_level="moderate",
            vegan=False,
            gluten_free=False,
            dairy_free=False,
            pescatarian=False
        )
        db.add(profile)
        db.commit()
            
    return user

async def main():
    print("Initializing Food App AI Agent CLI...")
    
    # Setup DB and User
    db = SessionLocal()
    try:
        user = await get_or_create_user(db)
        user_id = user.id
        print(f"Logged in as User ID: {user_id}")
    finally:
        db.close()
        
    session_id = None
    print("\n--- Start Chatting (type 'quit' or 'exit' to stop) ---")

    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ('quit', 'exit'):
                print("Goodbye!")
                break
            
            if not user_input:
                continue
                
            print("AI is thinking...", end="", flush=True)
            result = await agent_service.chat(user_id=user_id, message=user_input, session_id=session_id)
            print("\r" + " " * 20 + "\r", end="", flush=True) # Clear "thinking"
            
            print(f"AI: {result['response']}")
            
            # Update session ID to maintain context
            session_id = result.get('session_id')
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    asyncio.run(main())
