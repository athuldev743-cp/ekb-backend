from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from datetime import datetime, timedelta
import os

router = APIRouter()

# -----------------------------
# CONFIG
# -----------------------------
ADMIN_EMAIL = "athuldev743@gmail.com"      # change to your admin email
ADMIN_PASSWORD = "admin123"            # change to your strong password
ADMIN_SECRET_KEY = "your-secret-key"   # use strong secret in production
ALGORITHM = "HS256"
UPLOAD_DIR = "uploaded_images"

# create upload folder if not exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

# -----------------------------
# AUTH DEPENDENCY
# -----------------------------
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
        token = jwt.encode(
            {
                "sub": email,
                "role": "admin",
                "exp": datetime.utcnow() + timedelta(hours=2)
            },
            ADMIN_SECRET_KEY,
            algorithm=ALGORITHM
        )
        return {"access_token": token, "token_type": "bearer"}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# -----------------------------
# CREATE PRODUCT (ADMIN ONLY)
# -----------------------------
@router.post("/products")
async def create_product(
    name: str = Form(...),
    price: float = Form(...),
    description: str = Form(...),
    priority: int = Form(...),
    email: str = Form(...),
    image: UploadFile = File(...),
    admin=Depends(admin_required)  # only admin can access
):
    try:
        # save uploaded file locally
        file_location = os.path.join(UPLOAD_DIR, image.filename)
        with open(file_location, "wb") as f:
            f.write(await image.read())

        return {
            "status": "success",
            "file_path": file_location,
            "name": name,
            "price": price,
            "description": description,
            "priority": priority,
            "email": email
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
