from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.services.tools import ALL_TOOLS
from app.core.database import SessionLocal
from app.models.models import User, ChatSession, ChatMessage, OnboardingProfile
from sqlalchemy import select
import uuid
import os
import json

# Ensure OPENAI_API_KEY is set in environment
if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "sk-placeholder" # Placeholder to prevent crash on init if missing

class AgentService:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.tools = ALL_TOOLS
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an intelligent Food App Assistant. You have access to the user's pantry, meal plans, and shopping list. "
                       "You can help them manage their food, log meals, and suggest recipes. "
                       "User Context: {user_profile} "
                       "If the user profile is missing information (like gender, weight, goal), ask for it politely as part of onboarding. "
                       "Always extract the user_id from the context provided (it will be injected into tool calls). "
                       "If you need to perform an action like adding to pantry, use the appropriate tool. "
                       "You have access to the user's meal history and saved recipes via tools. "
                       "Use 'get_meal_history' to analyze past meals and 'get_saved_recipes' for scaling or cost comparison. "
                       "If the user asks to change their activity level, goal, or dietary preferences (vegan, gluten free, etc.), "
                       "YOU MUST use the 'update_user_profile' tool to persist the change. Do not just acknowledge it. "
                       "Be helpful, concise, and proactive."),
            ("system", "Current User ID: {user_id}"), # We'll inject this
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        self.agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)

    async def chat(self, user_id: int, message: str, session_id: str = None) -> Dict[str, Any]:
        """
        Process a chat message from a user.
        """
        db = SessionLocal()
        try:
            # 1. Get or Create Session
            if not session_id:
                session_id = str(uuid.uuid4())
                session = ChatSession(user_id=user_id, session=session_id, name="New Chat")
                db.add(session)
                db.commit()
            else:
                session = db.execute(select(ChatSession).where(ChatSession.session == session_id)).scalars().first()
                if not session:
                     # Fallback if ID sent but not found
                     session = ChatSession(user_id=user_id, session=session_id, name="New Chat")
                     db.add(session)
                     db.commit()

            # 2. Get User Profile
            profile_str = "No profile found."
            onboarding = db.execute(select(OnboardingProfile).where(OnboardingProfile.user_id == user_id)).scalars().first()
            if onboarding:
                profile_data = {
                    "gender": onboarding.gender,
                    "date_of_birth": str(onboarding.date_of_birth),
                    "current_height": f"{onboarding.current_height} {onboarding.current_height_unit}",
                    "current_weight": f"{onboarding.current_weight} {onboarding.current_weight_unit}",
                    "target_weight": f"{onboarding.target_weight} {onboarding.target_weight_unit}",
                    "goal": onboarding.goal,
                    "activity_level": onboarding.activity_level,
                    "dietary": {
                        "vegan": onboarding.vegan,
                        "gluten_free": onboarding.gluten_free,
                        "dairy_free": onboarding.dairy_free,
                        "pescatarian": onboarding.pescatarian
                    }
                }
                profile_str = json.dumps(profile_data)

            # 3. Retrieve History
            # For simplicity, we'll just grab the last N messages
            # In a real app, format this correctly for LangChain
            history_objs = db.execute(
                select(ChatMessage).where(ChatMessage.session_id == session.id).order_by(ChatMessage.created_at)
            ).scalars().all()
            
            chat_history = []
            for msg in history_objs:
                if msg.role == "user":
                    chat_history.append(("human", msg.content))
                else:
                    chat_history.append(("ai", msg.content))

            # 4. Invoke Agent
            response = await self.agent_executor.ainvoke({
                "input": message,
                "chat_history": chat_history,
                "user_id": user_id,
                "user_profile": profile_str
            })
            
            output = response["output"]

            # 4. Save Message & Response
            user_msg = ChatMessage(session_id=session.id, user_id=user_id, role="user", content=message)
            ai_msg = ChatMessage(session_id=session.id, user_id=user_id, role="assistant", content=output)
            
            db.add(user_msg)
            db.add(ai_msg)
            db.commit()

            return {
                "response": output,
                "session_id": session_id
            }

        finally:
            db.close()

agent_service = AgentService()
