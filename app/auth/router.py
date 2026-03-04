from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
import jwt

from google.oauth2 import id_token
from google.auth.transport import requests

from app.core.config import GOOGLE_CLIENT_ID, ADMIN_EMAIL, SECRET_KEY

router = APIRouter(prefix="/auth", tags=["auth"])

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
ISSUER = "ekabhumi-backend"


class GoogleTokenRequest(BaseModel):
    token: str


@router.post("/google")
def google_login(body: GoogleTokenRequest):
    # Verify Google ID token (audience = your client id)
    try:
        idinfo = id_token.verify_oauth2_token(
            body.token,
            requests.Request(),
            GOOGLE_CLIENT_ID,
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    email = (idinfo.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email not found in Google token")

    # Minimal role assignment: admin email from env (not hardcoded in code)
    role = "admin" if ADMIN_EMAIL and email == ADMIN_EMAIL.strip().lower() else "user"

    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    claims = {
        "sub": email,
        "role": role,
        "iss": ISSUER,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }

    access_token = jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": role,
        "email": email,
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }