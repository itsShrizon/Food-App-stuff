from fastapi import FastAPI
from app.api.v1 import meals, pantry, shopping, agent, onboarding
from app.core.database import engine, Base

# Create tables if they don't exist (for local testing mostly)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Food App AI API", version="1.0.0")

app.include_router(onboarding.router, prefix="/api/v1/onboarding", tags=["Onboarding"])
app.include_router(meals.router, prefix="/api/v1/meals", tags=["Meals"])
app.include_router(pantry.router, prefix="/api/v1/pantry", tags=["Pantry"])
app.include_router(shopping.router, prefix="/api/v1/shopping", tags=["Shopping"])
app.include_router(agent.router, prefix="/api/v1/agent", tags=["Agent"])

@app.get("/")
def root():
    return {"message": "Welcome to Food App AI API"}
