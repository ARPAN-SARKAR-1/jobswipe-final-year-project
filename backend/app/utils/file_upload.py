from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

BYTES_PER_MB = 1024 * 1024

IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
DOCUMENT_MIME_TYPES = {*IMAGE_MIME_TYPES, "application/pdf"}
DOCUMENT_EXTENSIONS = {*IMAGE_EXTENSIONS, ".pdf"}
RESUME_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
RESUME_EXTENSIONS = {".pdf", ".doc", ".docx"}

DISPLAY_TYPES = {
    "images": "JPG, PNG, WEBP",
    "documents": "PDF, JPG, PNG, WEBP",
    "resumes": "PDF, DOC, DOCX",
}

STUDENT_PROOF_TYPES = {
    "college_id_card",
    "library_card",
    "bonafide_certificate",
    "admission_proof",
    "fee_receipt",
}
CERTIFICATE_TYPES = {
    "graduation_marksheet",
    "degree_certificate",
    "provisional_certificate",
    "experience_letter",
    "relieving_letter",
    "offer_letter",
    "recommendation_letter",
    "reference_letter",
    "certificate",
}


class UploadRule:
    def __init__(
        self,
        label: str,
        max_mb: int,
        mime_types: set[str],
        extensions: set[str],
        display_types: str,
        subfolder: str,
    ) -> None:
        self.label = label
        self.max_mb = max_mb
        self.max_bytes = max_mb * BYTES_PER_MB
        self.mime_types = mime_types
        self.extensions = extensions
        self.display_types = display_types
        self.subfolder = subfolder


def image_extension(content_type: str | None, filename_extension: str | None) -> str:
    if filename_extension and filename_extension in IMAGE_EXTENSIONS:
        return ".jpg" if filename_extension == ".jpeg" else filename_extension
    return {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }.get(content_type or "", ".jpg")


def upload_extension(content_type: str | None, filename_extension: str | None) -> str:
    if filename_extension:
        if filename_extension == ".jpeg":
            return ".jpg"
        return filename_extension
    return {
        "application/pdf": ".pdf",
        "application/msword": ".doc",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }.get(content_type or "", ".bin")


def profile_photo_rule() -> UploadRule:
    return UploadRule(
        "profile photo",
        settings.max_profile_photo_mb,
        IMAGE_MIME_TYPES,
        IMAGE_EXTENSIONS,
        DISPLAY_TYPES["images"],
        "profile-pictures",
    )


def company_logo_rule() -> UploadRule:
    return UploadRule(
        "company logo",
        settings.max_company_logo_mb,
        IMAGE_MIME_TYPES,
        IMAGE_EXTENSIONS,
        DISPLAY_TYPES["images"],
        "company-logos",
    )


def resume_rule() -> UploadRule:
    return UploadRule(
        "resume",
        settings.max_resume_mb,
        RESUME_MIME_TYPES,
        RESUME_EXTENSIONS,
        DISPLAY_TYPES["resumes"],
        "resumes",
    )


def verification_document_rule(document_type: str | None = None) -> UploadRule:
    normalized_type = (document_type or "").strip().lower()
    if normalized_type in STUDENT_PROOF_TYPES:
        max_mb = settings.max_student_proof_mb
        label = "student proof"
    elif normalized_type in CERTIFICATE_TYPES:
        max_mb = settings.max_certificate_mb
        label = normalized_type.replace("_", " ") if normalized_type else "certificate"
    else:
        max_mb = settings.max_verification_document_mb
        label = normalized_type.replace("_", " ") if normalized_type else "verification document"
    return UploadRule(label, max_mb, DOCUMENT_MIME_TYPES, DOCUMENT_EXTENSIONS, DISPLAY_TYPES["documents"], "verification-documents")


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
    resource_type = "image" if (content_type or "").startswith("image/") else "raw"
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


async def read_limited_content(file: UploadFile, rule: UploadRule) -> bytes:
    content = bytearray()
    while chunk := await file.read(1024 * 1024):
        content.extend(chunk)
        if len(content) > rule.max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum allowed size for {rule.label} is {rule.max_mb} MB.",
            )
    return bytes(content)


def validate_upload_file(file: UploadFile, rule: UploadRule) -> str:
    filename_extension = Path(file.filename or "").suffix.lower()
    content_type = (file.content_type or "").lower()
    if filename_extension not in rule.extensions or content_type not in rule.mime_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {rule.display_types}.",
        )
    return upload_extension(content_type, filename_extension)


async def save_upload(file: UploadFile, rule: UploadRule) -> str:
    extension = validate_upload_file(file, rule)
    content = await read_limited_content(file, rule)

    if settings.cloudinary_enabled:
        return upload_to_cloudinary(content, rule.subfolder, extension, file.content_type)
    return save_local_upload(content, rule.subfolder, extension)


async def save_image(file: UploadFile, subfolder: str = "images") -> str:
    rule = UploadRule("image", settings.max_profile_photo_mb, IMAGE_MIME_TYPES, IMAGE_EXTENSIONS, DISPLAY_TYPES["images"], subfolder)
    return await save_upload(file, rule)


async def save_profile_photo(file: UploadFile) -> str:
    return await save_upload(file, profile_photo_rule())


async def save_company_logo(file: UploadFile) -> str:
    return await save_upload(file, company_logo_rule())


async def save_resume_pdf(file: UploadFile) -> str:
    return await save_upload(file, resume_rule())


async def save_verification_document(file: UploadFile, document_type: str | None = None) -> str:
    return await save_upload(file, verification_document_rule(document_type))
