
import asyncio
import os
import sys
from app.services.agent_service import agent_service

sys.path.append(os.getcwd())

async def test_pantry():
    print("Testing get_pantry_items...")
    # user_id 1 is the test user
    try:
        # We need to invoke the tool directly or via agent. 
        # Let's try invoking the tool function directly first to isolate DB access.
        from app.services.tools import get_pantry_items
        result = get_pantry_items.invoke({"user_id": 1})
        print(f"Tool Direct Result: {result}")
        
    except Exception as e:
        print(f"Tool Direct Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_pantry())
