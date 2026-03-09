from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
import jwt

from google.oauth2 import id_token
from google.auth.transport import requests

from app.core.config import GOOGLE_CLIENT_ID, ADMIN_EMAIL, SECRET_KEY

router = APIRouter(prefix="/auth", tags=["auth"])

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30          # 30 days
ISSUER = "ekabhumi-backend"


class GoogleTokenRequest(BaseModel):
    token: str


def _create_token(email: str, role: str) -> tuple[str, int]:
    """Returns (access_token, expires_in_seconds)"""
    now = datetime.now(timezone.utc)
    exp = now + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    claims = {
        "sub":  email,
        "role": role,
        "iss":  ISSUER,
        "iat":  int(now.timestamp()),
        "exp":  int(exp.timestamp()),
    }
    token = jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM)
    return token, ACCESS_TOKEN_EXPIRE_DAYS * 24 * 3600


@router.post("/google")
def google_login(body: GoogleTokenRequest):
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

    role = "admin" if ADMIN_EMAIL and email == ADMIN_EMAIL.strip().lower() else "user"

    access_token, expires_in = _create_token(email, role)

    return {
        "access_token": access_token,
        "token_type":   "bearer",
        "role":         role,
        "email":        email,
        "name":         idinfo.get("name", ""),
        "picture":      idinfo.get("picture", ""),
        "expires_in":   expires_in,
    }


# ── Token refresh endpoint ────────────────────────────────────────────────────
# Frontend calls this once on app load if token is within 7 days of expiry.
# Returns a fresh 30-day token — no re-login needed.
from fastapi import Header
from app.auth.jwt_utils import decode_jwt_from_header

@router.post("/refresh")
def refresh_token(
    authorization: str | None = Header(default=None, alias="Authorization")
):
    payload = decode_jwt_from_header(authorization)
    email   = payload.get("sub")
    role    = payload.get("role", "user")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")

    access_token, expires_in = _create_token(email, role)
    return {
        "access_token": access_token,
        "expires_in":   expires_in,
    }