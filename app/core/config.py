from dotenv import load_dotenv
import os

load_dotenv()  # loads .env into environment

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
SECRET_KEY = os.getenv("SECRET_KEY")

if not GOOGLE_CLIENT_ID:
    raise RuntimeError("GOOGLE_CLIENT_ID not set")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY not set")
