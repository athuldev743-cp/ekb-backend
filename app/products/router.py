from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product

router = APIRouter()


@router.get("/products")
def get_products(db: Session = Depends(get_db)):
    try:
        products = db.query(Product).order_by(Product.priority.asc()).all()
        return [
            {
                "id": p.id,
                "name": p.name,
                "price": float(p.price) if p.price else 0.0,
                "description": p.description or "",
                "quantity": int(p.quantity or 0),
                "image_url": p.image_url or "",
                "priority": p.priority or 100,
            }
            for p in products
        ]
    except Exception as e:
        # Don't lie to frontend by returning [].
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
        "description": product.description or "",
        "quantity": int(product.quantity or 0),
        "image_url": product.image_url or "",
        "priority": product.priority or 100,
    }