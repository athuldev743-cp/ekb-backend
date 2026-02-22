# auth/review.py
import os, time
from jose import jwt
from fastapi import APIRouter, HTTPException

router = APIRouter()

REVIEW_TOKEN = os.getenv("REVIEW_TOKEN", "")
JWT_SECRET = os.getenv("JWT_SECRET", "")
ALG = "HS256"

@router.get("/auth/review-login")
def review_login(token: str):
    if not REVIEW_TOKEN or not JWT_SECRET:
        raise HTTPException(status_code=500, detail="Server not configured")

    if token != REVIEW_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid review token")

    payload = {
        "sub": "razorpay-review-user",
        "role": "review",
        "exp": int(time.time()) + 30 * 60,
        "iat": int(time.time()),
    }

    access_token = jwt.encode(payload, JWT_SECRET, algorithm=ALG)
    return {"access_token": access_token, "token_type": "Bearer"}