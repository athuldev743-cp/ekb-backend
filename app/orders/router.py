# app/orders/router.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
import secrets

from app.auth.jwt_utils import user_required
from app.database import get_db
from app.models import Order, Product
from app.schemas import (
    PublicOrderCreate,
    PublicOrderResponse,
    PublicOrderCreateResponse,
    MyOrderResponse,
)

router = APIRouter()


def calculate_shipping(pincode: str):
    if not pincode or len(pincode) < 2:
        return 100.0
    prefix = pincode[:2]
    if prefix in ["67", "68", "69"]:
        return 50.0
    if prefix in ["50", "51", "52", "53", "56", "57", "58", "59", "60", "61", "62", "63", "64"]:
        return 80.0
    return 120.0


@router.post("/orders", response_model=PublicOrderCreateResponse)
def create_order(order_data: PublicOrderCreate, db: Session = Depends(get_db)):
    try:
        product = db.query(Product).filter(Product.id == order_data.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        qty = int(order_data.quantity or 0)
        if qty <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be > 0")

        unit_price = float(product.price or 0)
        if unit_price <= 0:
            raise HTTPException(status_code=400, detail="Invalid product price")

        shipping_fee = calculate_shipping(order_data.pincode)
        verified_total = (unit_price * qty) + float(shipping_fee)

        public_token = secrets.token_urlsafe(32)

        order = Order(
            public_token=public_token,
            product_id=product.id,
            product_name=product.name,
            quantity=qty,
            unit_price=unit_price,
            total_amount=verified_total,
            customer_name=order_data.customer_name,
            customer_email=order_data.customer_email,
            customer_phone=order_data.customer_phone,
            shipping_address=order_data.shipping_address,
            pincode=order_data.pincode,
            notes=order_data.notes or "",
            status="pending",
            payment_status="pending",
            order_date=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        return {"order": order, "public_token": public_token}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")


@router.get("/orders/{order_id}", response_model=PublicOrderResponse)
def get_order(
    order_id: int,
    token: str = Query(..., min_length=10),
    db: Session = Depends(get_db),
):
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.public_token == token)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Attach product image
    _attach_product_image(order, db)
    return order


@router.get("/orders/me", response_model=list[MyOrderResponse])
def list_my_orders(db: Session = Depends(get_db), user=Depends(user_required)):
    """
    Returns only PAID orders for the logged-in user, newest first.
    Attaches product image_url from the products table.
    """
    email = user["sub"]
    orders = (
        db.query(Order)
        .filter(
            Order.customer_email == email,
            Order.payment_status == "paid",          # ← only paid orders
        )
        .order_by(Order.id.desc())
        .all()
    )

    # Attach product images in one query
    product_ids = list({o.product_id for o in orders if o.product_id})
    products_map = {}
    if product_ids:
        products = db.query(Product).filter(Product.id.in_(product_ids)).all()
        products_map = {p.id: p for p in products}

    for order in orders:
        p = products_map.get(order.product_id)
        order.product_image_url = p.image_url if p else None

    return orders


# ── helper ────────────────────────────────────────────────────────────────────
def _attach_product_image(order: Order, db: Session):
    """Attach product_image_url as a transient attribute on the order object."""
    if not order.product_id:
        order.product_image_url = None
        return
    product = db.query(Product).filter(Product.id == order.product_id).first()
    order.product_image_url = product.image_url if product else None