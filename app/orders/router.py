from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Order
from app.schemas import OrderResponse, OrderCreate

router = APIRouter()

# -----------------------------
# PUBLIC ORDER ENDPOINTS ONLY
# -----------------------------
@router.post("/orders", response_model=OrderResponse)
def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    order_dict = order_data.dict()
    order = Order(**order_dict, status="pending")
    
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order