# app/auth/jwt_utils.py
from fastapi import Header, HTTPException
import os
import jwt

SECRET_KEY = os.getenv("SECRET_KEY", "test-secret-key-for-development")
ALGORITHM = "HS256"

def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    if authorization.startswith("Bearer "):
        token = authorization.split("Bearer ")[1].strip()
    else:
        token = authorization.strip()

    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    return token

def decode_jwt_from_header(authorization: str | None) -> dict:
    token = _extract_bearer_token(authorization)
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

def admin_required(authorization: str | None = Header(default=None)) -> dict:
    payload = decode_jwt_from_header(authorization)
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return payload