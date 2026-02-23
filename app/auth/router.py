# app/auth/router.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import jwt
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.database import get_db
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

class GoogleTokenRequest(BaseModel):
    token: str

@router.post("/google")
def google_login(request: GoogleTokenRequest):
    try:
        SECRET_KEY = os.getenv("SECRET_KEY", "test-secret-key-for-development")

        email = None
        role = "user"

        if len(request.token) > 100:
            # DEV ONLY: decode without verification
            try:
                decoded = jwt.decode(request.token, options={"verify_signature": False})
                email = decoded.get("email") or decoded.get("sub")
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid token")
        else:
            # test tokens only
            if request.token == "test-admin-token":
                email = "athuldev743@gmail.com"
            elif request.token == "test-user-token":
                email = "user@example.com"
            else:
                raise HTTPException(status_code=400, detail="Invalid token")

        if not email:
            raise HTTPException(status_code=400, detail="Invalid token")

        ADMIN_EMAILS = ["athuldev743@gmail.com"]
        if email in ADMIN_EMAILS:
            role = "admin"

        jwt_token = jwt.encode(
            {"sub": email, "role": role, "email": email, "exp": datetime.utcnow() + timedelta(hours=24)},
            SECRET_KEY,
            algorithm="HS256",
        )

        return {"access_token": jwt_token, "token_type": "bearer", "role": role, "email": email}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in google_login: {str(e)}")
        raise HTTPException(status_code=400, detail="Google login failed")
    
