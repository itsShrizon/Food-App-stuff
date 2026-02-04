from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.services.agent_service import agent_service

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    session_id: str = None
    user_id: int # In a real app, this comes from auth token

@router.post("/chat")
async def chat_with_agent(request: ChatRequest):
    try:
        response = await agent_service.chat(
            user_id=request.user_id,
            message=request.message,
            session_id=request.session_id
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
