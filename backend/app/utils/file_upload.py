from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

MAX_IMAGE_BYTES = 2 * 1024 * 1024
MAX_PDF_BYTES = 5 * 1024 * 1024
IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


async def save_upload(file: UploadFile, subfolder: str, allowed_types: dict[str, str], max_bytes: int) -> str:
    content = await file.read()
    if len(content) > max_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size exceeds the allowed limit")

    extension = allowed_types.get(file.content_type or "")
    if extension is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type")

    target_dir = settings.upload_path / subfolder
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{extension}"
    target = target_dir / filename
    target.write_bytes(content)
    return f"/uploads/{subfolder}/{filename}"


async def save_image(file: UploadFile, subfolder: str) -> str:
    return await save_upload(file, subfolder, IMAGE_TYPES, MAX_IMAGE_BYTES)


async def save_resume_pdf(file: UploadFile) -> str:
    if file.filename and not Path(file.filename).suffix.lower() == ".pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resume must be a PDF")
    return await save_upload(file, "resumes", {"application/pdf": ".pdf"}, MAX_PDF_BYTES)
