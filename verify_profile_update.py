
import asyncio
import os
import sys
from sqlalchemy import select
from app.services.tools import update_user_profile
from app.core.database import SessionLocal
from app.models.models import OnboardingProfile

sys.path.append(os.getcwd())

async def verify_update():
    print("Testing update_user_profile tool...")
    user_id = 1
    
    # 1. Check Initial State
    db = SessionLocal()
    initial_profile = db.execute(select(OnboardingProfile).where(OnboardingProfile.user_id == user_id)).scalars().first()
    print(f"Initial Activity Level: {initial_profile.activity_level}")
    db.close()
    
    # 2. Invoke Tool to Change to 'very active' and 'vegan'
    result = update_user_profile.invoke({"user_id": user_id, "activity_level": "very active", "vegan": True})
    print(f"Tool Result: {result}")
    
    # 3. Verify Persistence
    db = SessionLocal()
    updated_profile = db.execute(select(OnboardingProfile).where(OnboardingProfile.user_id == user_id)).scalars().first()
    print(f"Updated Activity Level: {updated_profile.activity_level}")
    print(f"Updated Vegan Status: {updated_profile.vegan}")
    db.close()
    
    if updated_profile.activity_level == "very active" and updated_profile.vegan:
        print("SUCCESS: Profile updated in DB.")
    else:
        print("FAILURE: Profile not updated.")

if __name__ == "__main__":
    asyncio.run(verify_update())
