from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app import models  # noqa: F401

app = FastAPI()

import warnings
warnings.filterwarnings(
    "ignore",
    message="pkg_resources is deprecated as an API.*"
)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

origins = [
    "https://ekabhumi.vercel.app",
    "https://ekabhumih.in",
    "https://www.ekabhumih.in",
    "http://172.26.224.1:5500",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.products import router as product_router
from app.orders import router as order_router
from app.admin import router as admin_router
from app.auth.router import router as auth_router
from app.payments.router import router as payments_router
from app.reviews.router import router as reviews_router


app.include_router(reviews_router)
app.include_router(product_router)
app.include_router(order_router)
app.include_router(admin_router, prefix="/admin")
app.include_router(auth_router)
app.include_router(payments_router)
app.include_router(reviews_router)                        # ← NEW

@app.get("/")
def root():
    return {"message": "EKB Backend API", "status": "running"}

@app.get("/health")
def health():
    return {"ok": True}