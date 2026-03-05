

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.auth.jwt_utils import admin_required
from app.database import get_db
from app.models import Review

# If you are adding to your existing admin router, just copy the route
# functions below into app/admin.py. Do NOT re-create the router.
router = APIRouter(tags=["admin-reviews"])


class ReviewAdminOut(BaseModel):
    id: int
    user_email: str
    user_name: str
    product_id: Optional[int]
    product_name: Optional[str]
    rating: int
    text: str
    approved: bool
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/reviews", response_model=list[ReviewAdminOut])
def admin_list_reviews(
    db: Session = Depends(get_db),
    _: dict = Depends(admin_required),
):
    """All reviews (pending + approved) for admin."""
    return db.query(Review).order_by(Review.created_at.desc()).all()


@router.patch("/reviews/{review_id}/approve")
def admin_approve_review(
    review_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(admin_required),
):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    review.approved = True
    db.commit()
    return {"message": "Review approved"}


@router.delete("/reviews/{review_id}")
def admin_delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(admin_required),
):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    db.delete(review)
    db.commit()
    return {"message": "Review deleted"}