from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Product
from app.dependencies.admin import admin_only
from typing import List

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
# ADMIN: UPDATE PRODUCT
# -----------------------------
@router.put("/{product_id}")
def update_product(
    product_id: int,
    name: str = None,
    price: float = None,
    description: str = None,
    image_url: str = None,
    priority: int = None,
    db: Session = Depends(get_db),
    admin = Depends(admin_only)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if name is not None:
        product.name = name
    if price is not None:
        product.price = price
    if description is not None:
        product.description = description
    if image_url is not None:
        product.image_url = image_url
    if priority is not None:
        product.priority = priority
    
    db.commit()
    db.refresh(product)
    return product

# -----------------------------
# ADMIN: DELETE PRODUCT
# -----------------------------
@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin = Depends(admin_only)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}

# -----------------------------
# ADMIN: GET ALL PRODUCTS (with admin view)
# -----------------------------
@router.get("/admin", response_model=List[Product])
def get_admin_products(
    db: Session = Depends(get_db),
    admin = Depends(admin_only)
):
    return db.query(Product).order_by(Product.priority.asc()).all()

# -----------------------------
# PUBLIC: ALL PRODUCTS
# -----------------------------
@router.get("/")
def get_products(db: Session = Depends(get_db)):
    return db.query(Product).order_by(Product.priority.asc()).all()

# -----------------------------
# PUBLIC: SINGLE PRODUCT
# -----------------------------
@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

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