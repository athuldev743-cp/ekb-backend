# app/cloudinary_setup.py
import cloudinary
import cloudinary.uploader
import cloudinary.api
from fastapi import UploadFile
import os

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

async def upload_to_cloudinary(file: UploadFile, folder: str = "ekabhumi/products") -> str:
    try:
        # Read file content
        file_content = await file.read()
        
        # Upload file to Cloudinary
        result = cloudinary.uploader.upload(
            file_content,
            folder=folder,
            public_id=file.filename.split('.')[0],
            overwrite=True,
            resource_type="auto"
        )
        
        # Return the secure URL
        return result.get("secure_url", "")
    except Exception as e:
        print(f"Cloudinary upload error: {e}")
        raise e

async def delete_from_cloudinary(image_url: str) -> bool:
    try:
        if not image_url:
            return True
            
        # Extract public_id from Cloudinary URL
        # Example: https://res.cloudinary.com/cloudname/image/upload/v1234567/folder/filename.jpg
        if "cloudinary.com" not in image_url:
            return True
            
        # Get the path after /upload/
        upload_index = image_url.find("/upload/") + 8
        path_with_version = image_url[upload_index:]
        
        # Remove version if present (v1234567/)
        if path_with_version.startswith("v"):
            path_without_version = "/".join(path_with_version.split("/")[1:])
        else:
            path_without_version = path_with_version
        
        # Remove file extension
        public_id = path_without_version.split(".")[0]
        
        # Delete from Cloudinary
        result = cloudinary.uploader.destroy(public_id)
        return result.get("result") == "ok"
    except Exception as e:
        print(f"Cloudinary delete error: {e}")
        return False