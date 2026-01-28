from fastapi import APIRouter, HTTPException
from google.oauth2 import id_token
from google.auth.transport import requests

from app.core.security import create_access_token
from app.core.config import GOOGLE_CLIENT_ID, ADMIN_EMAIL

router = APIRouter()

@router.post("/google")
def google_login(token: str):
    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )

        email = idinfo.get("email")
        role = "admin" if email == ADMIN_EMAIL else "user"

        jwt_token = create_access_token({
            "sub": email,
            "role": role
        })

        return {
            "access_token": jwt_token,
            "role": role
        }

    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Google token")
