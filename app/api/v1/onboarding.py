from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import date
import uuid

from app.core.database import get_db
from app.models.models import User, OnboardingProfile, MetabolicProfile
from app.services.onboarding.calculator import calculate_metabolic_profile
from app.services.onboarding.utils import calculate_age
from app.services.onboarding.flow import onboarding as onboarding_flow
from app.services.onboarding.config import ONBOARDING_FIELDS

router = APIRouter()

# In-memory session storage (use Redis in production)
ONBOARDING_SESSIONS: Dict[str, Dict[str, Any]] = {}


class ChatRequest(BaseModel):
    """Request for conversational onboarding."""
    user_id: int
    message: str
    session_id: Optional[str] = None


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


# ============================================================================
# CONVERSATIONAL ONBOARDING ENDPOINTS
# ============================================================================

@router.post("/chat/start")
def start_onboarding_chat(user_id: int, db: Session = Depends(get_db)):
    """Start a fresh onboarding conversation session."""
    # Verify user exists
    user = db.execute(select(User).where(User.id == user_id)).scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    session_id = str(uuid.uuid4())
    ONBOARDING_SESSIONS[session_id] = {
        "user_id": user_id,
        "conversation_history": [],
        "collected_data": {},
    }
    
    # Return initial greeting
    return {
        "session_id": session_id,
        "message": "Hi there! To get started, what's your gender? (male, female, or others)",
        "is_complete": False,
        "progress": {"collected": 0, "total": len(ONBOARDING_FIELDS)},
        "collected_data": {},
    }


@router.post("/chat")
def chat_onboarding(request: ChatRequest, db: Session = Depends(get_db)):
    """Process a message in the onboarding conversation."""
    # Verify user exists
    user = db.execute(select(User).where(User.id == request.user_id)).scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get or create session
    session_id = request.session_id
    if not session_id or session_id not in ONBOARDING_SESSIONS:
        session_id = str(uuid.uuid4())
        ONBOARDING_SESSIONS[session_id] = {
            "user_id": request.user_id,
            "conversation_history": [],
            "collected_data": {},
        }
    
    session = ONBOARDING_SESSIONS[session_id]
    
    # Verify session belongs to this user
    if session["user_id"] != request.user_id:
        raise HTTPException(status_code=403, detail="Session does not belong to this user")
    
    # Process message through onboarding flow
    result = onboarding_flow(
        user_message=request.message,
        conversation_history=session["conversation_history"],
        collected_data=session["collected_data"],
    )
    
    # Update session
    session["conversation_history"] = result["conversation_history"]
    session["collected_data"] = result["collected_data"]
    
    # Calculate progress
    collected_count = len([f for f in ONBOARDING_FIELDS if f in result["collected_data"]])
    
    response = {
        "session_id": session_id,
        "message": result["message"],
        "is_complete": result["is_complete"],
        "progress": {"collected": collected_count, "total": len(ONBOARDING_FIELDS)},
        "next_field": result.get("next_field"),
        "collected_data": result["collected_data"],
        "metabolic_profile": result.get("metabolic_profile"),
    }
    
    # If complete, save to database and cleanup session
    if result["is_complete"] and result.get("db_format"):
        db_data = result["db_format"]
        response["db_format"] = db_data
        # Optionally auto-save here (or let frontend call POST / explicitly)
        del ONBOARDING_SESSIONS[session_id]
    
    return response


@router.get("/chat/{session_id}")
def get_session_state(session_id: str):
    """Get the current state of an onboarding session."""
    if session_id not in ONBOARDING_SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    session = ONBOARDING_SESSIONS[session_id]
    collected_count = len([f for f in ONBOARDING_FIELDS if f in session["collected_data"]])
    
    return {
        "session_id": session_id,
        "user_id": session["user_id"],
        "progress": {"collected": collected_count, "total": len(ONBOARDING_FIELDS)},
        "collected_data": session["collected_data"],
        "conversation_history": session["conversation_history"],
    }

