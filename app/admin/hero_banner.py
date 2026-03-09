from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
import time

from app.database import get_db
from app.models import HeroBanner
from app.cloudinary_setup import upload_to_cloudinary, delete_from_cloudinary
from app.auth.jwt_utils import admin_required

router = APIRouter()

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB


async def _validate_image(image: UploadFile) -> None:
    content_type = (image.content_type or "").lower()
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid image type. Use JPEG/PNG/WebP")
    contents = await image.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty image file")
    if len(contents) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail="Image too large (max 5 MB)")
    await image.seek(0)


# ─────────────────────────────────────────────
# GET /hero-banner  — public, no auth required
# ─────────────────────────────────────────────
@router.get("/hero-banner")
def get_hero_banner(db: Session = Depends(get_db)):
    banner = db.query(HeroBanner).filter(HeroBanner.id == 1).first()
    if not banner:
        return {"desktop_image": None, "mobile_image": None}
    return {
        "desktop_image": banner.desktop_image,
        "mobile_image":  banner.mobile_image,
    }


# ─────────────────────────────────────────────
# PUT /admin/hero-banner  — admin only
# ─────────────────────────────────────────────
@router.put("/hero-banner")
async def update_hero_banner(
    desktop_image: Optional[UploadFile] = File(None),
    mobile_image:  Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    admin=Depends(admin_required),
):
    if not desktop_image and not mobile_image:
        raise HTTPException(status_code=400, detail="Provide at least one image")

    # Fetch or create the single banner row
    banner = db.query(HeroBanner).filter(HeroBanner.id == 1).first()
    if not banner:
        banner = HeroBanner(id=1)
        db.add(banner)

    result = {}

    if desktop_image:
        await _validate_image(desktop_image)
        # Delete old Cloudinary asset if present
        if banner.desktop_image and "cloudinary.com" in (banner.desktop_image or ""):
            try:
                await delete_from_cloudinary(banner.desktop_image)
            except Exception:
                pass
        url = await upload_to_cloudinary(desktop_image, folder="ekabhumi/hero")
        banner.desktop_image = url
        result["desktop_image"] = url

    if mobile_image:
        await _validate_image(mobile_image)
        if banner.mobile_image and "cloudinary.com" in (banner.mobile_image or ""):
            try:
                await delete_from_cloudinary(banner.mobile_image)
            except Exception:
                pass
        url = await upload_to_cloudinary(mobile_image, folder="ekabhumi/hero")
        banner.mobile_image = url
        result["mobile_image"] = url

    db.commit()
    db.refresh(banner)

    return {"success": True, **result}