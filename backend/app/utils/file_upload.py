from pathlib import Path
import re
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

try:
    import magic  # type: ignore
except ImportError:  # pragma: no cover - optional production hardening dependency
    magic = None

MAX_IMAGE_BYTES = 2 * 1024 * 1024
MAX_PDF_BYTES = 5 * 1024 * 1024
IMAGE_TYPES = {
    "image/jpeg": {".jpg", ".jpeg"},
    "image/png": {".png"},
    "image/webp": {".webp"},
}
PDF_TYPES = {"application/pdf": {".pdf"}}
ACADEMIC_DOCUMENT_TYPES = {**PDF_TYPES, **IMAGE_TYPES}
DANGEROUS_EXTENSIONS = {
    ".bat",
    ".cmd",
    ".crt",
    ".exe",
    ".html",
    ".jar",
    ".js",
    ".key",
    ".pem",
    ".php",
    ".py",
    ".sh",
    ".zip",
}


def invalid_file_type() -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type.")


def file_too_large() -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size exceeds allowed limit.")


def sanitize_original_filename(filename: str | None, allowed_extensions: set[str]) -> str:
    raw_name = (filename or "").strip()
    if not raw_name or "/" in raw_name or "\\" in raw_name:
        raise invalid_file_type()
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", raw_name)
    suffix = Path(safe_name).suffix.lower()
    if suffix in DANGEROUS_EXTENSIONS or suffix not in allowed_extensions:
        raise invalid_file_type()
    return suffix


def safe_display_filename(filename: str | None) -> str:
    raw_name = (filename or "document").strip().replace("\\", "_").replace("/", "_")
    safe_name = re.sub(r"[^A-Za-z0-9._ -]", "_", raw_name).strip(" .")
    return safe_name[:255] or "document"


def sniff_content_type(content: bytes) -> str | None:
    if magic is not None:
        try:
            detected = magic.from_buffer(content, mime=True)
            return detected.lower() if detected else None
        except Exception:
            pass
    if content.startswith(b"%PDF-"):
        return "application/pdf"
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp"
    return None


async def save_upload_with_metadata(file: UploadFile, subfolder: str, allowed_types: dict[str, set[str]], max_bytes: int) -> dict[str, str | int]:
    normalized_types = {key.lower(): {suffix.lower() for suffix in value} for key, value in allowed_types.items()}
    allowed_extensions = {suffix for suffixes in normalized_types.values() for suffix in suffixes}
    extension = sanitize_original_filename(file.filename, allowed_extensions)
    content_type = (file.content_type or "").split(";", 1)[0].strip().lower()
    allowed_for_mime = normalized_types.get(content_type)
    if allowed_for_mime is None or extension not in allowed_for_mime:
        raise invalid_file_type()

    content = await file.read()
    if len(content) > max_bytes:
        raise file_too_large()
    detected_content_type = sniff_content_type(content)
    if detected_content_type is None:
        raise invalid_file_type()
    detected_allowed_extensions = normalized_types.get(detected_content_type)
    if detected_allowed_extensions is None or extension not in detected_allowed_extensions:
        raise invalid_file_type()

    upload_root = settings.upload_path.resolve()
    target_dir = (upload_root / subfolder).resolve()
    try:
        target_dir.relative_to(upload_root)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Upload storage path is invalid") from exc
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{extension}"
    target = target_dir / filename
    target.write_bytes(content)
    return {
        "url": f"/uploads/{subfolder}/{filename}",
        "stored_filename": filename,
        "original_filename": safe_display_filename(file.filename),
        "mime_type": detected_content_type,
        "file_size": len(content),
    }


async def save_upload(file: UploadFile, subfolder: str, allowed_types: dict[str, set[str]], max_bytes: int) -> str:
    metadata = await save_upload_with_metadata(file, subfolder, allowed_types, max_bytes)
    return str(metadata["url"])


async def save_image(file: UploadFile, subfolder: str) -> str:
    return await save_upload(file, subfolder, IMAGE_TYPES, MAX_IMAGE_BYTES)


async def save_resume_pdf(file: UploadFile) -> str:
    url = await save_upload(file, "resumes", PDF_TYPES, MAX_PDF_BYTES)
    filename = url.rsplit("/", 1)[-1]
    return f"/api/files/resumes/{filename}"


async def save_jobseeker_document(file: UploadFile, resume_only: bool = False) -> dict[str, str | int]:
    metadata = await save_upload_with_metadata(
        file,
        "jobseeker-documents",
        PDF_TYPES if resume_only else ACADEMIC_DOCUMENT_TYPES,
        MAX_PDF_BYTES,
    )
    filename = str(metadata["stored_filename"])
    metadata["url"] = f"/api/files/jobseeker-documents/{filename}"
    return metadata
