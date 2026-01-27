from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Product
from app.dependencies.admin import admin_only

router = APIRouter()


# -----------------------------
# ADMIN: CREATE PRODUCT
# -----------------------------
@router.post("/")
def create_product(
    name: str,
    price: float,
    description: str = "",
    image_url: str = "",
    priority: int = 100,
    db: Session = Depends(get_db),
    admin = Depends(admin_only)
):
    product = Product(
        name=name,
        price=price,
        description=description,
        image_url=image_url,
        priority=priority
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


# -----------------------------
# PUBLIC: ALL PRODUCTS
# -----------------------------
@router.get("/")
def get_products(db: Session = Depends(get_db)):
    return db.query(Product).order_by(Product.priority.asc()).all()


# -----------------------------
# PUBLIC: HOMEPAGE PRODUCT
# -----------------------------
@router.get("/homepage")
def homepage_product(db: Session = Depends(get_db)):
    return (
        db.query(Product)
        .order_by(Product.priority.asc())
        .first()
    )
