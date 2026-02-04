from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import date

from app.core.database import get_db
from app.models.models import User, OnboardingProfile, MetabolicProfile
from app.services.onboarding.calculator import calculate_metabolic_profile
from app.services.onboarding.utils import calculate_age

router = APIRouter()

class OnboardingRequest(BaseModel):
    user_id: int
    gender: str
    date_of_birth: date
    current_height: float
    current_height_unit: str = "cm"
    current_weight: float
    current_weight_unit: str = "kg"
    target_weight: float
    target_weight_unit: str = "kg"
    goal: str
    activity_level: str
    vegan: bool = False
    gluten_free: bool = False
    dairy_free: bool = False
    pescatarian: bool = False

@router.get("/{user_id}")
def get_profile(user_id: int, db: Session = Depends(get_db)):
    """Get the onboarding profile for a user."""
    profile = db.execute(select(OnboardingProfile).where(OnboardingProfile.user_id == user_id)).scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.post("/")
def create_or_update_profile(data: OnboardingRequest, db: Session = Depends(get_db)):
    """Create or update the onboarding profile and recalculate metabolic metrics."""
    # Check if user exists
    user = db.execute(select(User).where(User.id == data.user_id)).scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update/Create Onboarding Profile
    profile = db.execute(select(OnboardingProfile).where(OnboardingProfile.user_id == data.user_id)).scalars().first()
    if not profile:
        profile = OnboardingProfile(user_id=data.user_id)
        db.add(profile)
    
    # Map fields
    profile.gender = data.gender
    profile.date_of_birth = data.date_of_birth
    profile.current_height = data.current_height
    profile.current_height_unit = data.current_height_unit
    profile.current_weight = data.current_weight
    profile.current_weight_unit = data.current_weight_unit
    profile.target_weight = data.target_weight
    profile.target_weight_unit = data.target_weight_unit
    profile.goal = data.goal
    profile.activity_level = data.activity_level
    profile.vegan = data.vegan
    profile.gluten_free = data.gluten_free
    profile.dairy_free = data.dairy_free
    profile.pescatarian = data.pescatarian
    
    db.commit()
    db.refresh(profile)

    # Calculate Metabolic Profile
    try:
        age = calculate_age(str(data.date_of_birth))
        metrics = calculate_metabolic_profile(
            gender=data.gender,
            weight=data.current_weight,
            weight_unit=data.current_weight_unit,
            height=data.current_height,
            height_unit=data.current_height_unit,
            age=age,
            activity_level=data.activity_level,
            goal=data.goal,
            target_weight=data.target_weight,
            target_weight_unit=data.target_weight_unit
        )
        
        met_profile = db.execute(select(MetabolicProfile).where(MetabolicProfile.user_id == data.user_id)).scalars().first()
        if not met_profile:
            met_profile = MetabolicProfile(user_id=data.user_id)
            db.add(met_profile)
            
        met_profile.bmr = metrics["bmr"]
        met_profile.tdee = metrics["tdee"]
        met_profile.daily_calorie_target = metrics["daily_calorie_target"]
        met_profile.protein_g = metrics["protein_g"]
        met_profile.carbs_g = metrics["carbs_g"]
        met_profile.fats_g = metrics["fats_g"]
        
        db.commit()
        db.refresh(met_profile)
        
        return {
            "onboarding": profile,
            "metabolic": met_profile,
            "message": "Profile updated successfully"
        }
        
    except Exception as e:
        # Don't fail the whole request if calculator fails, but warn
        return {
            "onboarding": profile,
            "warning": f"Could not calculate metabolic profile: {str(e)}",
            "message": "Profile updated, but metrics calculation failed."
        }
