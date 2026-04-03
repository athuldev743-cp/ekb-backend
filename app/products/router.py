from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Product

router = APIRouter()

@router.get("/products")
def get_products(db: Session = Depends(get_db)):
    try:
        # 1. Fetch from DB first
        products = db.query(Product).order_by(Product.priority.asc()).all()
        
        # 2. Loop over the 'products' list, NOT the function name
        return [
            {
                "id": p.id,
                "name": p.name,
                "price": float(p.price) if p.price else 0.0,
                # Added original_price here
                "original_price": float(p.original_price) if p.original_price else None,
                "description": p.description or "",
                "quantity": int(p.quantity or 0),
                "image_url": p.image_url or "",
                "priority": p.priority or 100,
            }
            for p in products  # Fixed: used 'products' variable
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch products") from e


@router.get("/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return {
        "id": product.id,
        "name": product.name,
        "price": float(product.price) if product.price else 0.0,
        # Added original_price here too so the Detail page matches the List page
        "original_price": float(product.original_price) if product.original_price else None,
        "description": product.description or "",
        "quantity": int(product.quantity or 0),
        "image_url": product.image_url or "",
        "priority": product.priority or 100,
    }