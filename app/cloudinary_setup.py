import os
import re
import uuid
import cloudinary
import cloudinary.uploader
from fastapi import UploadFile, HTTPException


def _require_env(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise RuntimeError(f"{name} is not set")
    return val


# Configure Cloudinary (fail fast if missing)
cloudinary.config(
    cloud_name=_require_env("CLOUDINARY_CLOUD_NAME"),
    api_key=_require_env("CLOUDINARY_API_KEY"),
    api_secret=_require_env("CLOUDINARY_API_SECRET"),
    secure=True,
)

_FOLDER_RE = re.compile(r"^[a-zA-Z0-9/_-]+$")


def _safe_folder(folder: str) -> str:
    folder = (folder or "").strip().strip("/")
    if not folder:
        return "ekabhumi/products"
    if not _FOLDER_RE.match(folder):
        # prevent weird chars in folder path
        return "ekabhumi/products"
    return folder


async def upload_to_cloudinary(file: UploadFile, folder: str = "ekabhumi/products") -> str:
    try:
        folder = _safe_folder(folder)

        # read bytes
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Empty upload")

        # unique id (no collisions)
        public_id = str(uuid.uuid4())

        result = cloudinary.uploader.upload(
            file_bytes,
            folder=folder,
            public_id=public_id,
            overwrite=False,          # do not overwrite existing
            resource_type="image",    # force image only
        )

        url = result.get("secure_url")
        if not url:
            raise HTTPException(status_code=500, detail="Cloudinary upload failed")

        return url

    except HTTPException:
        raise
    except Exception as e:
        # don't leak internals to client; raise a clean error
        raise HTTPException(status_code=500, detail="Cloudinary upload error") from e


async def delete_from_cloudinary(image_url: str) -> bool:
    try:
        if not image_url or "cloudinary.com" not in image_url:
            return True

        # Extract public_id from URL
        # Works for: .../upload/v123/folder/public_id.ext
        upload_marker = "/upload/"
        idx = image_url.find(upload_marker)
        if idx == -1:
            return True

        path = image_url[idx + len(upload_marker):]  # v123/folder/public_id.ext
        parts = path.split("/")

        # drop version folder if present (v123...)
        if parts and parts[0].startswith("v") and parts[0][1:].isdigit():
            parts = parts[1:]

        if not parts:
            return True

        # remove extension
        last = parts[-1]
        public_id_no_ext = last.rsplit(".", 1)[0]
        public_id = "/".join(parts[:-1] + [public_id_no_ext])

        res = cloudinary.uploader.destroy(public_id, resource_type="image")
        return (res or {}).get("result") in {"ok", "not found"}

    except Exception:
        return False