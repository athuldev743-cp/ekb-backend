from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, VARCHAR, Index, Boolean, func
from app.database import Base
from sqlalchemy import Column, Integer, String, Text, Numeric, CheckConstraint


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    google_id = Column(String, unique=True, nullable=True)
    role = Column(String, default="user", nullable=False)
    password_hash = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(255), nullable=False)

    description = Column(Text, nullable=True)

    price = Column(Numeric(10, 2), nullable=False)
    original_price = Column(Numeric(10, 2), nullable=True)

    quantity = Column(Integer, default=0, nullable=False)

    image_url = Column(String(500), nullable=True)

    priority = Column(Integer, default=2, nullable=False, index=True)

    __table_args__ = (
        CheckConstraint("price > 0", name="price_positive"),
        CheckConstraint(
            "original_price IS NULL OR original_price >= price",
            name="valid_discount"
        ),
    )

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    public_token = Column(String(128), nullable=False, index=True, unique=True)
    product_id = Column(Integer, nullable=False)
    product_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    customer_name = Column(String, nullable=False)
    customer_email = Column(String, nullable=False, index=True)
    customer_phone = Column(String, nullable=False)
    shipping_address = Column(Text, nullable=False)
    pincode = Column(String(10), nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String, default="pending", nullable=False)
    payment_status = Column(String, default="pending", nullable=False)
    razorpay_order_id = Column(String, nullable=True, index=True)
    razorpay_payment_id = Column(String, nullable=True, index=True)
    payment_method = Column(String, nullable=True)
    order_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, nullable=False, index=True)
    user_name = Column(String, nullable=False)
    product_id = Column(Integer, nullable=True, index=True)
    product_name = Column(String, nullable=True)
    rating = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    approved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# ── NEW: Blog model ──────────────────────────────────────────────────────────
class Blog(Base):
    __tablename__ = "blogs"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, nullable=False)
    excerpt = Column(Text, nullable=False)

    category = Column(String, nullable=False, default="General")
    read_time = Column(String, nullable=False, default="5 min read")

    image_url = Column(String, nullable=True)
    href = Column(String, nullable=True)

    order = Column(Integer, default=1, nullable=False, index=True)

    publish_date = Column(DateTime, nullable=True)  # None = publish immediately

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


Index("ix_orders_payment_status", Order.payment_status)
Index("ix_orders_status", Order.status)
Index("ix_reviews_approved", Review.approved)
Index("ix_blogs_order", Blog.order)


class HeroBanner(Base):
    __tablename__ = "hero_banner"

    id             = Column(Integer, primary_key=True, default=1)
    desktop_image  = Column(String(500), nullable=True)
    mobile_image   = Column(String(500), nullable=True)
    updated_at     = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())