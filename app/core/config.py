from pathlib import Path
import os
from dotenv import load_dotenv

# Load .env from project root (EKa_bhumi_backend/.env)
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # app/core/config.py -> project root
load_dotenv(BASE_DIR / ".env")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
SECRET_KEY = os.getenv("SECRET_KEY")

if not GOOGLE_CLIENT_ID:
    raise RuntimeError("GOOGLE_CLIENT_ID not set")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY not set")

# Basic secret hardening (prevents stupidly weak secrets)
if len(SECRET_KEY) < 32:
    raise RuntimeError("SECRET_KEY is too short (use at least 32 characters)")

# Optional: enforce admin email existence (recommended if you use email-based admin)
if not ADMIN_EMAIL:
    # If you truly want no admin in some environments, remove this check.
    raise RuntimeError("ADMIN_EMAIL not set")