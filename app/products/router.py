from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Product
from app.schemas import ProductResponse

router = APIRouter()

# -----------------------------
# PUBLIC PRODUCT ENDPOINTS ONLY
# -----------------------------
@router.get("/products", response_model=List[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    return db.query(Product).order_by(Product.priority.asc()).all()

@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.get("/products/homepage/", response_model=ProductResponse)
def homepage_product(db: Session = Depends(get_db)):
    return db.query(Product).order_by(Product.priority.asc()).first()