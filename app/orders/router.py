from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Order
from app.dependencies.admin import admin_only
from typing import List

router = APIRouter()

# -----------------------------
# ADMIN: GET ALL ORDERS
# -----------------------------
@router.get("/admin")
def get_all_orders(db: Session = Depends(get_db), admin=Depends(admin_only)):
    return db.query(Order).order_by(Order.created_at.desc()).all()

# -----------------------------
# ADMIN: UPDATE ORDER STATUS
# -----------------------------
@router.put("/{order_id}/status")
def update_order_status(
    order_id: int,
    status: str,
    db: Session = Depends(get_db),
    admin=Depends(admin_only)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = status
    db.commit()
    db.refresh(order)

    return {
        "message": "Order status updated",
        "order_id": order_id,
        "status": status
    }

# -----------------------------
# ADMIN: DELETE ORDER
# -----------------------------
@router.delete("/{order_id}")
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    admin=Depends(admin_only)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    db.delete(order)
    db.commit()
    return {"message": "Order deleted successfully"}

# -----------------------------
# PUBLIC: CREATE ORDER
# -----------------------------
@router.post("/")
def create_order(
    user_email: str,
    product_name: str,
    quantity: int = 1,
    total_price: float = 0,
    db: Session = Depends(get_db)
):
    order = Order(
        user_email=user_email,
        product_name=product_name,
        quantity=quantity,
        total_price=total_price,
        status="pending"  # Add default status
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

# -----------------------------
# PUBLIC: GET ORDER (for order confirmation)
# -----------------------------
@router.get("/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order