from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app import models  # noqa: F401

import warnings
warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*")

app = FastAPI()

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
from app.admin.admin_review import router as admin_reviews_router
from app.admin.admin_blog import router as blog_router
from app.admin.hero_banner import router as hero_banner_router   # ← NEW
from app.auth.router import router as auth_router
from app.payments.router import router as payments_router
from app.reviews.router import router as reviews_router

# Public blog endpoint
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Blog
from fastapi import Depends
from datetime import datetime

@app.get("/blogs")
def public_list_blogs(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    blogs = (
        db.query(Blog)
        .filter((Blog.publish_date == None) | (Blog.publish_date <= now))
        .order_by(Blog.order.asc())
        .limit(4)
        .all()
    )
    return [
        {
            "id": b.id,
            "title": b.title,
            "excerpt": b.excerpt,
            "category": b.category,
            "read_time": b.read_time,
            "image_url": b.image_url or "",
            "href": b.href or "",
            "order": b.order,
            "publish_date": b.publish_date.isoformat() if b.publish_date else None,
        }
        for b in blogs
    ]


app.include_router(reviews_router)
app.include_router(product_router)
app.include_router(order_router)
app.include_router(admin_router,         prefix="/admin")
app.include_router(admin_reviews_router, prefix="/admin")
app.include_router(blog_router,          prefix="/admin")
app.include_router(hero_banner_router,   prefix="/admin")   # ← mounts PUT  /admin/hero-banner
app.include_router(hero_banner_router)                      # ← mounts GET  /hero-banner  (public)
app.include_router(auth_router)
app.include_router(payments_router)

@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return {"message": "EKB Backend API", "status": "running"}

@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"ok": True}