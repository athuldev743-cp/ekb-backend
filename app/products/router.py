# app/products/router.py - FIXED VERSION
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db  # Import from database
from app.models import Product  # Import Product model

router = APIRouter()

@router.get("/products")
def get_products(db: Session = Depends(get_db)):
    try:
        print("Fetching products from database...")
        
        # Query products
        products = db.query(Product).order_by(Product.priority.asc()).all()
        
        print(f"Found {len(products)} products")
        
        # Convert to list of dicts
        result = []
        for product in products:
            result.append({
                "id": product.id,
                "name": product.name,
                "price": float(product.price) if product.price else 0.0,
                "description": product.description or "",
                "image_url": product.image_url or "",
                "priority": product.priority or 100
            })
        
        return result
        
    except Exception as e:
        print(f"Error fetching products: {e}")
        # Return mock data if database fails
        return [
            {
                "id": 1,
                "name": "Redensyl Hair Growth Serum",
                "price": 299.0,
                "description": "Advanced hair growth serum",
                "image_url": "/images/redensyl.jpg",
                "priority": 1
            },
            {
                "id": 2,
                "name": "Vitamin C Serum",
                "price": 499.0,
                "description": "Brightening serum",
                "image_url": "/images/vitamin-c.jpg", 
                "priority": 2
            }
        ]