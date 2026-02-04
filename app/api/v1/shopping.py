from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import ShoppingItem
from pydantic import BaseModel

router = APIRouter()

class ShoppingItemCreate(BaseModel):
    name: str
    quantity: float
    unit: str
    user_id: int

@router.get("/")
def get_shopping_list(user_id: int = 1, db: Session = Depends(get_db)):
    items = db.query(ShoppingItem).filter(ShoppingItem.user_id == user_id).all()
    return items

@router.post("/")
def add_shopping_item(item: ShoppingItemCreate, db: Session = Depends(get_db)):
    db_item = ShoppingItem(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
