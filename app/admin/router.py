# app/admin/router.py - UPDATED (change route names)
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Header
import os
from jose import jwt

router = APIRouter()

# -----------------------------
# CONFIG
# -----------------------------
ADMIN_EMAIL = "athuldev743@gmail.com"
ADMIN_SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-development")
ALGORITHM = "HS256"

UPLOAD_DIR = "uploaded_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# -----------------------------
# SIMPLE AUTH (for testing)
# -----------------------------
def admin_required(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization header")
    
    # Accept any token for testing
    if authorization.startswith("Bearer "):
        token = authorization.split("Bearer ")[1]
    else:
        token = authorization
    
    # For testing, accept any non-empty token
    if not token:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return {"email": ADMIN_EMAIL, "role": "admin"}

# -----------------------------
# CREATE PRODUCT (Admin only)
# -----------------------------
@router.post("/create-product")  # Changed from /products to /create-product
async def create_product(
    name: str = Form(...),
    price: float = Form(...),
    description: str = Form(...),
    priority: int = Form(...),
    email: str = Form(...),
    image: UploadFile = File(...),
    admin=Depends(admin_required)
):
    file_path = os.path.join(UPLOAD_DIR, image.filename)
    with open(file_path, "wb") as f:
        content = await image.read()
        f.write(content)
    
    return {
        "status": "success", 
        "file": file_path,
        "product": {
            "name": name,
            "price": price,
            "description": description,
            "priority": priority
        }
    }

# -----------------------------
# GET ALL PRODUCTS (Admin view)
# -----------------------------
@router.get("/admin-products")  # Changed from /products to /admin-products
async def get_admin_products(admin=Depends(admin_required)):
    # For now, return mock data
    return [
        {"id": 1, "name": "Admin Product 1", "price": 100, "description": "Test"},
        {"id": 2, "name": "Admin Product 2", "price": 200, "description": "Test 2"}
    ]

# -----------------------------
# UPDATE PRODUCT
# -----------------------------
@router.put("/update-product/{product_id}")  # Changed route
async def update_product(
    product_id: int,
    name: str = Form(None),
    price: float = Form(None),
    description: str = Form(None),
    priority: int = Form(None),
    image: UploadFile = File(None),
    admin=Depends(admin_required)
):
    return {"message": f"Product {product_id} updated"}

# -----------------------------
# DELETE PRODUCT
# -----------------------------
@router.delete("/delete-product/{product_id}")  # Changed route
async def delete_product(product_id: int, admin=Depends(admin_required)):
    return {"message": f"Product {product_id} deleted"}

# -----------------------------
# GET ALL ORDERS
# -----------------------------
@router.get("/orders")
async def get_admin_orders(admin=Depends(admin_required)):
    return [
        {"id": 1, "customer_email": "user1@example.com", "status": "pending", "total": 300},
        {"id": 2, "customer_email": "user2@example.com", "status": "completed", "total": 500}
    ]