from fastapi import Header, HTTPException
import jwt

from app.core.config import SECRET_KEY

ALGORITHM = "HS256"
ISSUER = "ekabhumi-backend"


def decode_jwt_from_header(authorization: str | None) -> dict:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization format")

    token = authorization.split("Bearer ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    if payload.get("iss") != ISSUER:
        raise HTTPException(status_code=401, detail="Invalid token issuer")

    return payload


def user_required(
    authorization: str | None = Header(default=None, alias="Authorization")
) -> dict:
    payload = decode_jwt_from_header(authorization)
    if not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return payload


def admin_required(
    authorization: str | None = Header(default=None, alias="Authorization")
) -> dict:
    payload = decode_jwt_from_header(authorization)
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return payload