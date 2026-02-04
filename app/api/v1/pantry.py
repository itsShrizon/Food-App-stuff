from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import PantryItem
from pydantic import BaseModel

router = APIRouter()

class PantryItemCreate(BaseModel):
    item_name: str
    quantity: float
    unit: str
    user_id: int

@router.get("/")
def get_pantry(user_id: int = 1, db: Session = Depends(get_db)):
    items = db.query(PantryItem).filter(PantryItem.user_id == user_id).all()
    return items

@router.post("/")
def add_pantry_item(item: PantryItemCreate, db: Session = Depends(get_db)):
    db_item = PantryItem(**item.dict(), low_inventory_threshold=0)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
