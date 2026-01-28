# app/schemas.py - Complete version
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# -------- Google Auth Input --------
class GoogleAuthRequest(BaseModel):
    id_token: str   # token received from Google frontend

# -------- User Output --------
class UserResponse(BaseModel):
    id: int
    name: str
    email: str  # Changed from EmailStr to avoid email-validator dependency
    role: str

    class Config:
        orm_mode = True

# -------- Auth Response --------
class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# -------- Optional: Admin Creation --------
class AdminCreate(BaseModel):
    name: str
    email: str

# -------- Product Schemas --------
class ProductBase(BaseModel):
    name: str
    price: float
    description: Optional[str] = ""
    image_url: Optional[str] = ""
    priority: Optional[int] = 100

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    priority: Optional[int] = None

class ProductResponse(ProductBase):
    id: int
    created_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

# -------- Order Schemas --------
class OrderBase(BaseModel):
    user_email: str
    product_name: str
    quantity: Optional[int] = 1
    total_price: Optional[float] = 0

class OrderCreate(OrderBase):
    pass

class OrderUpdate(BaseModel):
    status: Optional[str] = None

class OrderResponse(OrderBase):
    id: int
    status: str
    created_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True