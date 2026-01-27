from pydantic import BaseModel, EmailStr
from typing import Optional


# -------- Google Auth Input --------
class GoogleAuthRequest(BaseModel):
    id_token: str   # token received from Google frontend


# -------- User Output --------
class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True


# -------- Auth Response --------
class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# -------- Optional: Admin Creation --------
class AdminCreate(BaseModel):
    name: str
    email: EmailStr

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    stock: int
    category: str

class OrderCreate(BaseModel):
    user_id: int
    total_amount: float

