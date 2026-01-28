from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status
from datetime import datetime
import os
from jose import jwt

router = APIRouter()

# -----------------------------
# CONFIG
# -----------------------------
ADMIN_EMAIL = "athuldev743@gmail.com"
ADMIN_PASSWORD = "admin123"
ADMIN_SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

UPLOAD_DIR = "uploaded_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# -----------------------------
# ADMIN TOKEN DEPENDENCY
# -----------------------------
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/admin/login")

def admin_required(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, ADMIN_SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not an admin")
        return payload
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# -----------------------------
# ADMIN LOGIN
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
    admin=Depends(admin_required)
):
    file_path = os.path.join(UPLOAD_DIR, image.filename)
    with open(file_path, "wb") as f:
        f.write(await image.read())
    return {"status": "success", "file": file_path}

# -----------------------------
# GET ALL PRODUCTS
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
