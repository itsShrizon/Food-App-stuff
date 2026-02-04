from fastapi import APIRouter

router = APIRouter()

@router.get("/today")
def get_todays_meals():
    return {"message": "Today's meals (stub)"}
