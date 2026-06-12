from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

MAX_IMAGE_BYTES = 2 * 1024 * 1024
MAX_PDF_BYTES = 5 * 1024 * 1024
IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


def upload_to_cloudinary(content: bytes, subfolder: str, extension: str, content_type: str | None) -> str:
    try:
        import cloudinary
        import cloudinary.uploader
    except ImportError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cloudinary support is not installed") from exc

    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )
    resource_type = "raw" if content_type == "application/pdf" else "image"
    public_id = f"{uuid4().hex}{extension}" if resource_type == "raw" else uuid4().hex
    stream = BytesIO(content)
    stream.name = f"{public_id}{'' if public_id.endswith(extension) else extension}"
    result = cloudinary.uploader.upload(
        stream,
        folder=f"swipe-for-success/{subfolder}",
        public_id=public_id,
        resource_type=resource_type,
        overwrite=False,
    )
    secure_url = result.get("secure_url")
    if not secure_url:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cloudinary upload failed")
    return str(secure_url)


def save_local_upload(content: bytes, subfolder: str, extension: str) -> str:
    target_dir = settings.upload_path / subfolder
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{extension}"
    target = target_dir / filename
    target.write_bytes(content)
    return f"/uploads/{subfolder}/{filename}"


async def save_upload(file: UploadFile, subfolder: str, allowed_types: dict[str, str], max_bytes: int) -> str:
    content = await file.read()
    if len(content) > max_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size exceeds the allowed limit")

    extension = allowed_types.get(file.content_type or "")
    if extension is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type")

    if settings.cloudinary_enabled:
        return upload_to_cloudinary(content, subfolder, extension, file.content_type)
    return save_local_upload(content, subfolder, extension)


async def save_image(file: UploadFile, subfolder: str) -> str:
    return await save_upload(file, subfolder, IMAGE_TYPES, MAX_IMAGE_BYTES)


async def save_resume_pdf(file: UploadFile) -> str:
    if file.filename and not Path(file.filename).suffix.lower() == ".pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resume must be a PDF")
    return await save_upload(file, "resumes", {"application/pdf": ".pdf"}, MAX_PDF_BYTES)
