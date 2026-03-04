from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime


# -----------------------------
# USERS / AUTH
# -----------------------------
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    expires_in: int


# -----------------------------
# PRODUCTS
# -----------------------------
class ProductBase(BaseModel):
    name: str
    price: float
    description: Optional[str] = ""
    quantity: Optional[int] = 0
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
    quantity: Optional[int] = None


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


# -----------------------------
# ORDERS: PUBLIC INPUT
# -----------------------------
class PublicOrderCreate(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1)

    customer_name: str
    customer_email: EmailStr
    customer_phone: str

    shipping_address: str
    pincode: str
    notes: Optional[str] = None


# -----------------------------
# ORDERS: PUBLIC RESPONSE (SAFE)
# -----------------------------
class PublicOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int

    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    total_amount: float

    status: str
    payment_status: str

    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None

    order_date: datetime
    updated_at: datetime


class PublicOrderCreateResponse(BaseModel):
    # Return token only once on order creation.
    order: PublicOrderResponse
    public_token: str


# -----------------------------
# ORDERS: AUTHENTICATED "MY ORDER" RESPONSE (FULL FOR OWNER)
# -----------------------------
class MyOrderResponse(PublicOrderResponse):
    customer_name: str
    customer_email: EmailStr
    customer_phone: str
    shipping_address: str
    pincode: str
    notes: Optional[str] = None


# -----------------------------
# ORDERS: ADMIN RESPONSE (FULL PII)
# -----------------------------
class AdminOrderResponse(MyOrderResponse):
    pass