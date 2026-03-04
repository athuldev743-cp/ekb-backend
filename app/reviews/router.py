from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from app.auth.jwt_utils import user_required
from app.database import get_db
from app.models import Review, Order

router = APIRouter(prefix="/reviews", tags=["reviews"])

APPROVED_STATUSES = {"confirmed", "approved", "shipped", "out_for_delivery", "delivered"}


# ── schemas ──────────────────────────────────────────────────────────────────

class ReviewCreate(BaseModel):
    product_id: Optional[int] = None
    rating: int = Field(..., ge=1, le=5)
    text: str = Field(..., min_length=5, max_length=1000)


class ReviewPublic(BaseModel):
    id: int
    user_name: str
    product_id: Optional[int]
    product_name: Optional[str]
    rating: int
    text: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── endpoints ─────────────────────────────────────────────────────────────────

@router.post("", status_code=201)
def create_review(
    body: ReviewCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(user_required),
):
    email = user["sub"]

    # Check user has at least one paid + approved order
    qualifying_order = (
        db.query(Order)
        .filter(
            Order.customer_email == email,
            Order.payment_status == "paid",
        )
        .all()
    )

    has_qualifying = any(
        str(o.status or "").lower() in APPROVED_STATUSES
        for o in qualifying_order
    )

    if not has_qualifying:
        raise HTTPException(
            status_code=403,
            detail="You can only review after a confirmed purchase.",
        )

    # One review per user (to keep it simple; remove if you want per-product reviews)
    existing = db.query(Review).filter(Review.user_email == email).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail="You have already submitted a review.",
        )

    # Resolve product name if product_id given
    product_name = None
    if body.product_id:
        from app.models import Product
        product = db.query(Product).filter(Product.id == body.product_id).first()
        product_name = product.name if product else None

    review = Review(
        user_email=email,
        user_name=user.get("name") or email.split("@")[0],
        product_id=body.product_id,
        product_name=product_name,
        rating=body.rating,
        text=body.text,
        approved=False,
    )

    db.add(review)
    db.commit()
    db.refresh(review)

    return {"message": "Review submitted. It will appear after admin approval.", "id": review.id}


@router.get("", response_model=list[ReviewPublic])
def get_approved_reviews(db: Session = Depends(get_db)):
    return (
        db.query(Review)
        .filter(Review.approved == True)  # noqa: E712
        .order_by(Review.created_at.desc())
        .all()
    )