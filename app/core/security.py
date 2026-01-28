from datetime import datetime, timedelta
from jose import jwt
from app.core.config import SECRET_KEY

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 2

def create_access_token(data: dict):
    to_encode = data.copy()
    to_encode.update({
        "exp": datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
