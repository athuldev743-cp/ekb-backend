# app/auth/router.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import jwt
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.database import get_db   # ✅ must exist in app/database.py
from app.models import User       # ✅ your models.py User class

router = APIRouter(prefix="/auth", tags=["auth"])

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


class GoogleTokenRequest(BaseModel):
    token: str


@router.post("/google")
def google_login(request: GoogleTokenRequest):
    try:
        print(f"Auth request received, token length: {len(request.token)}")

        # For development/testing, accept ANY token
        SECRET_KEY = os.getenv("SECRET_KEY", "test-secret-key-for-development")

        # Try to decode if it looks like a JWT
        email = "test@example.com"
        role = "user"

        if len(request.token) > 100:
            # Might be a real Google token
            try:
                # Try to decode as JWT (without verification for testing)
                decoded = jwt.decode(request.token, options={"verify_signature": False})
                email = decoded.get("email") or decoded.get("sub") or "user@example.com"
            except Exception:
                email = "user@example.com"
        else:
            # Short token, probably test token
            if request.token == "test-admin-token":
                email = "athuldev743@gmail.com"
                role = "admin"
            elif request.token == "test-user-token":
                email = "user@example.com"
                role = "user"
            else:
                email = f"{request.token}@example.com"

        # Check if admin
        ADMIN_EMAILS = ["athuldev743@gmail.com"]
        if email in ADMIN_EMAILS:
            role = "admin"

        # Create JWT token
        jwt_token = jwt.encode(
            {
                "sub": email,
                "role": role,
                "email": email,
                "exp": datetime.utcnow() + timedelta(hours=24),
            },
            SECRET_KEY,
            algorithm="HS256",
        )

        print(f"Generated JWT for {email} as {role}")

        return {
            "access_token": jwt_token,
            "token_type": "bearer",
            "role": role,
            "email": email,
        }

    except Exception as e:
        print(f"Error in google_login: {str(e)}")
        # Always return a valid response for testing
        return {
            "access_token": "mock.jwt.token.for.testing",
            "token_type": "bearer",
            "role": "admin",
            "email": "athuldev743@gmail.com",
        }


# ✅ NEW: Reviewer login (email + password)
class ReviewerLoginRequest(BaseModel):
    email: str
    password: str


@router.post("/reviewer-login")
def reviewer_login(request: ReviewerLoginRequest, db: Session = Depends(get_db)):
    SECRET_KEY = os.getenv("SECRET_KEY", "test-secret-key-for-development")

    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if user.role != "reviewer":
        raise HTTPException(status_code=403, detail="Not allowed")

    if not user.password_hash:
        raise HTTPException(status_code=400, detail="Password not set")

    if not pwd.verify(request.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    jwt_token = jwt.encode(
        {
            "sub": user.email,
            "role": user.role,
            "email": user.email,
            "exp": datetime.utcnow() + timedelta(hours=24),
        },
        SECRET_KEY,
        algorithm="HS256",
    )

    return {
        "access_token": jwt_token,
        "token_type": "bearer",
        "role": user.role,
        "email": user.email,
    }