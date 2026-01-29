from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status, Header
from datetime import datetime
import os
from jose import jwt
from google.oauth2 import id_token
from google.auth.transport import requests

router = APIRouter()

# -----------------------------
# CONFIG
# -----------------------------
ADMIN_EMAIL = "athuldev743@gmail.com"
ADMIN_PASSWORD = "admin123"
ADMIN_SECRET_KEY = os.getenv("your-secret-key")  # Should match your security.py
ALGORITHM = "HS256"
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")  # Make sure this is set

UPLOAD_DIR = "uploaded_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# -----------------------------
# TOKEN VERIFICATION
# -----------------------------
def verify_token(token: str):
    # Try to verify as Google token first
    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )
        email = idinfo.get("email")
        role = "admin" if email == ADMIN_EMAIL else "user"
        return {"sub": email, "role": role, "email": email, "source": "google"}
    except:
        # If not Google token, try as JWT token
        try:
            payload = jwt.decode(token, ADMIN_SECRET_KEY, algorithms=[ALGORITHM])
            return {**payload, "source": "jwt"}
        except:
            return None

# -----------------------------
# ADMIN AUTH DEPENDENCY (ACCEPTS BOTH TOKEN TYPES)
# -----------------------------
def admin_required(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization header")
    
    # Extract token from "Bearer <token>" or use as is
    if authorization.startswith("Bearer "):
        token = authorization.split("Bearer ")[1]
    else:
        token = authorization
    
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Check if user is admin
    if payload.get("role") != "admin" or payload.get("email") != ADMIN_EMAIL:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return payload

# -----------------------------
# ADMIN LOGIN (KEEP FOR BACKWARD COMPATIBILITY)
# -----------------------------
@router.post("/login")
def admin_login(email: str = Form(...), password: str = Form(...)):
    if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
        token = jwt.encode({
            "sub": email,
            "role": "admin"
        }, ADMIN_SECRET_KEY, algorithm=ALGORITHM)
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

# -----------------------------
# CREATE PRODUCT
# -----------------------------
@router.post("/products")
async def create_product(
    name: str = Form(...),
    price: float = Form(...),
    description: str = Form(...),
    priority: int = Form(...),
    email: str = Form(...),
    image: UploadFile = File(...),
    admin=Depends(admin_required)  # Now accepts both token types
):
    file_path = os.path.join(UPLOAD_DIR, image.filename)
    with open(file_path, "wb") as f:
        f.write(await image.read())
    return {"status": "success", "file": file_path}

# -----------------------------
# GET ALL PRODUCTS (FOR ADMIN)
# -----------------------------
@router.get("/products")
async def get_admin_products(admin=Depends(admin_required)):
    return [
        {"id": 1, "name": "Product 1", "price": 100, "description": "Test"},
        {"id": 2, "name": "Product 2", "price": 200, "description": "Test 2"}
    ]

# -----------------------------
# UPDATE PRODUCT
# -----------------------------
@router.put("/products/{product_id}")
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
@router.delete("/products/{product_id}")
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