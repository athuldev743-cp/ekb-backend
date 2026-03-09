from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models import Blog
from app.cloudinary_setup import upload_to_cloudinary, delete_from_cloudinary
from app.auth.jwt_utils import admin_required

# No hardcoded /admin prefix — main.py registers this with prefix="/admin"
router = APIRouter()

MAX_IMAGE_BYTES   = 5 * 1024 * 1024
ALLOWED_IMG_TYPES = {"image/jpeg", "image/png", "image/webp"}


async def _validate_image(image: UploadFile) -> None:
    if not image:
        raise HTTPException(400, "Image is required")
    content_type = (image.content_type or "").lower()
    if content_type not in ALLOWED_IMG_TYPES:
        raise HTTPException(400, "Invalid image type. Use JPEG/PNG/WebP")
    contents = await image.read()
    if not contents:
        raise HTTPException(400, "Empty image file")
    if len(contents) > MAX_IMAGE_BYTES:
        raise HTTPException(400, "Image too large (max 5MB)")
    await image.seek(0)


def _blog_dict(b: Blog) -> dict:
    return {
        "id":           b.id,
        "title":        b.title,
        "excerpt":      b.excerpt,
        "category":     b.category,
        "read_time":    b.read_time,
        "image_url":    b.image_url or "",
        "href":         b.href or "",
        "order":        b.order,
        "publish_date": b.publish_date.isoformat() if b.publish_date else None,
        "created_at":   b.created_at.isoformat() if b.created_at else None,
        "updated_at":   b.updated_at.isoformat() if b.updated_at else None,
    }


# GET /admin/blogs — all blogs including scheduled
@router.get("/blogs")
def admin_list_blogs(db: Session = Depends(get_db), admin=Depends(admin_required)):
    blogs = db.query(Blog).order_by(Blog.order.asc()).all()
    return [_blog_dict(b) for b in blogs]






# POST /admin/blogs — create
@router.post("/blogs")
async def create_blog(
    title: str = Form(...),
    excerpt: str = Form(...),
    category: str = Form("General"),
    read_time: str = Form("5 min read"),
    href: Optional[str] = Form(None),
    order: int = Form(1),
    publish_date: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    admin=Depends(admin_required),
):
    if order < 1 or order > 4:
        raise HTTPException(400, "Order must be between 1 and 4")

    existing = db.query(Blog).filter(Blog.order == order).first()
    if existing:
        raise HTTPException(400, "This blog slot is already used")

    image_url = None
    if image and image.filename:
        await _validate_image(image)
        image_url = await upload_to_cloudinary(image, folder="ekabhumi/blogs")

    parsed_date = None
    if publish_date:
        try:
            parsed_date = datetime.fromisoformat(publish_date)
        except ValueError:
            raise HTTPException(400, "Invalid publish_date format")

    blog = Blog(
        title=title.strip(),
        excerpt=excerpt.strip(),
        category=category.strip() or "General",
        read_time=read_time.strip() or "5 min read",
        href=href.strip() if href else None,
        order=order,
        image_url=image_url,
        publish_date=parsed_date,
    )
    db.add(blog)
    db.commit()
    db.refresh(blog)
    return {"status": "success", "blog": _blog_dict(blog)}
# PUT /admin/blogs/{id} — update
@router.put("/blogs/{blog_id}")
async def update_blog(
    blog_id: int,
    title: Optional[str] = Form(None),
    excerpt: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    read_time: Optional[str] = Form(None),
    href: Optional[str] = Form(None),
    order: Optional[int] = Form(None),
    publish_date: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    admin=Depends(admin_required),
):
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(404, "Blog not found")

    if order is not None:
        if order < 1 or order > 4:
            raise HTTPException(400, "Order must be between 1 and 4")

        existing = (
            db.query(Blog)
            .filter(Blog.order == order, Blog.id != blog_id)
            .first()
        )
        if existing:
            raise HTTPException(400, "This blog slot is already used")

        blog.order = order

    if title is not None:
        blog.title = title.strip()
    if excerpt is not None:
        blog.excerpt = excerpt.strip()
    if category is not None:
        blog.category = category.strip()
    if read_time is not None:
        blog.read_time = read_time.strip()
    if href is not None:
        blog.href = href.strip() or None

    if publish_date is not None:
        if publish_date == "":
            blog.publish_date = None
        else:
            try:
                blog.publish_date = datetime.fromisoformat(publish_date)
            except ValueError:
                raise HTTPException(400, "Invalid publish_date format")

    if image and image.filename:
        await _validate_image(image)
        if blog.image_url and "cloudinary.com" in blog.image_url:
            try:
                await delete_from_cloudinary(blog.image_url)
            except Exception:
                pass
        blog.image_url = await upload_to_cloudinary(image, folder="ekabhumi/blogs")

    blog.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(blog)
    return {"status": "success", "blog": _blog_dict(blog)}

# DELETE /admin/blogs/{id}
@router.delete("/blogs/{blog_id}")
async def delete_blog(
    blog_id: int,
    db: Session = Depends(get_db),
    admin=Depends(admin_required),
):
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(404, "Blog not found")

    if blog.image_url and "cloudinary.com" in blog.image_url:
        try: await delete_from_cloudinary(blog.image_url)
        except Exception: pass

    db.delete(blog)
    db.commit()
    return {"status": "success", "message": f"Blog {blog_id} deleted"}