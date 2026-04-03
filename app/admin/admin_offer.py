from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Product
from pydantic import BaseModel

router = APIRouter(prefix="/admin/offers", tags=["Admin Offers"])

class SetOfferRequest(BaseModel):
    product_id: int
    mrp: float        # The high price (to be crossed out)
    offer_price: float # The low price (the active one)

@router.post("/set-discount")
def set_discount(req: SetOfferRequest, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == req.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product.original_price = req.mrp
    product.price = req.offer_price
    
    db.commit()
    return {"status": "success", "message": f"Discount set for {product.name}"}

@router.post("/remove-discount/{product_id}")
def remove_discount(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        product.original_price = None
        db.commit()
    return {"status": "discount removed"}