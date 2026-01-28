from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Product
from app.schemas import ProductResponse
from app.dependencies.admin import admin_only

router = APIRouter()

# -----------------------------
# ADMIN PRODUCT ENDPOINTS (at /admin/products)
# -----------------------------
@router.post("/admin/products")
def create_product(
    name: str = Form(...),
    price: float = Form(...),
    description: str = Form(""),
    image_url: str = Form(""),
    priority: int = Form(100),
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

@router.get("/admin/products", response_model=List[ProductResponse])
def get_admin_products(db: Session = Depends(get_db), admin=Depends(admin_only)):
    return db.query(Product).order_by(Product.priority.asc()).all()

@router.put("/admin/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    name: str = Form(None),
    price: float = Form(None),
    description: str = Form(None),
    image_url: str = Form(None),
    priority: int = Form(None),
    db: Session = Depends(get_db),
    admin = Depends(admin_only)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if name is not None: product.name = name
    if price is not None: product.price = price
    if description is not None: product.description = description
    if image_url is not None: product.image_url = image_url
    if priority is not None: product.priority = priority
    
    db.commit()
    db.refresh(product)
    return product

@router.delete("/admin/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), admin=Depends(admin_only)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}

# -----------------------------
# PUBLIC PRODUCT ENDPOINTS (at /products)
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