from dataclasses import dataclass
from urllib.parse import urlparse

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.company_profile import CompanyProfile
from app.models.enums import JobCareerLinkStatus, JobSeekerCategory, StudentVerificationStatus
from app.models.job_seeker_profile import JobSeekerProfile
from app.models.recruiter_company_member import RecruiterCompanyMember
from app.models.user import User
from app.models.user_document import UserDocument

STUDENT_PROOF_DOCUMENTS = {
    "COLLEGE_ID_CARD",
    "LIBRARY_CARD",
    "BONAFIDE_CERTIFICATE",
    "ADMISSION_PROOF",
    "FEE_RECEIPT",
    "college_id_card",
    "library_card",
    "bonafide_certificate",
    "admission_proof",
    "fee_receipt",
}

KNOWN_ATS_DOMAINS = {
    "greenhouse.io",
    "boards.greenhouse.io",
    "lever.co",
    "jobs.lever.co",
    "workdayjobs.com",
    "myworkdayjobs.com",
    "icims.com",
    "smartrecruiters.com",
    "ashbyhq.com",
    "bamboohr.com",
    "jobvite.com",
    "successfactors.com",
    "taleo.net",
}


@dataclass
class CompletionResult:
    is_complete: bool
    missing_fields: list[str]
    completion_percentage: int


@dataclass
class CareerLinkResult:
    status: str
    warning: str | None = None


def present(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def _completion(required: list[tuple[str, bool]]) -> CompletionResult:
    missing = [label for label, ok in required if not ok]
    total = len(required) or 1
    percentage = round(((total - len(missing)) / total) * 100)
    return CompletionResult(is_complete=not missing, missing_fields=missing, completion_percentage=percentage)


def has_student_proof(db: Session, user_id: int) -> bool:
    count = db.scalar(
        select(func.count(UserDocument.id))
        .where(UserDocument.owner_user_id == user_id)
        .where(UserDocument.document_type.in_(STUDENT_PROOF_DOCUMENTS))
    )
    return bool(count)


def check_job_seeker_profile_completion(db: Session, user: User) -> CompletionResult:
    profile: JobSeekerProfile | None = db.scalar(select(JobSeekerProfile).where(JobSeekerProfile.user_id == user.id))
    required: list[tuple[str, bool]] = [
        ("full name", present(user.name)),
        ("verified email", bool(user.email_verified)),
        ("phone number", bool(profile and present(profile.phone))),
        ("job seeker category", bool(profile and present(profile.job_seeker_category))),
        ("skills", bool(profile and present(profile.skills))),
        ("resume", bool(profile and present(profile.resume_pdf_url))),
    ]

    category = profile.job_seeker_category if profile else None
    if category == JobSeekerCategory.UNDERGRADUATE.value:
        required.extend(
            [
                ("college name", present(profile.college_name)),
                ("university name", present(profile.university_name)),
                ("course or degree", present(profile.course_name) or present(profile.degree_name)),
                ("branch or department", present(profile.department_or_branch)),
                ("current year or semester", present(profile.current_year_or_semester)),
                ("expected passing year", present(profile.expected_passing_year)),
                (
                    "student proof document",
                    profile.student_verification_status
                    in {StudentVerificationStatus.STUDENT_PENDING.value, StudentVerificationStatus.STUDENT_VERIFIED.value}
                    or has_student_proof(db, user.id),
                ),
            ]
        )
    elif category == JobSeekerCategory.GRADUATE_FRESHER.value:
        required.extend(
            [
                ("highest degree", present(profile.highest_degree)),
                ("college name", present(profile.college_name)),
                ("university name", present(profile.university_name)),
                ("graduation year", present(profile.graduation_year)),
                ("specialization or branch", present(profile.specialization_or_branch)),
                (
                    "projects, certifications, or fresher skills",
                    present(profile.project_links) or present(profile.certifications) or present(profile.fresher_skills) or present(profile.skills),
                ),
            ]
        )
    elif category == JobSeekerCategory.GRADUATE_EXPERIENCED.value:
        required.extend(
            [
                ("total experience", profile.total_experience_years is not None),
                ("current or last company", present(profile.current_or_last_company)),
                ("current or last role", present(profile.current_or_last_role)),
                (
                    "tools, technologies, or responsibilities",
                    present(profile.tools_technologies) or present(profile.key_responsibilities),
                ),
            ]
        )
    elif profile is not None:
        required.append(("category details", False))

    return _completion(required)


def ensure_job_seeker_can_apply(db: Session, user: User) -> CompletionResult:
    result = check_job_seeker_profile_completion(db, user)
    if not result.is_complete:
        missing = ", ".join(result.missing_fields[:8])
        if len(result.missing_fields) > 8:
            missing += ", and more"
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Complete your profile before applying. Missing: {missing}.",
        )
    return result


def check_company_profile_completion(company: CompanyProfile, membership: RecruiterCompanyMember | None = None) -> CompletionResult:
    required = [
        ("company name", present(company.company_name)),
        ("industry", present(company.industry)),
        ("company size", present(company.company_size)),
        ("headquarters or location", present(company.headquarters) or present(company.location)),
        ("company website", present(company.website)),
        ("career page", present(company.career_page_url)),
        ("company description", present(company.about_company) or present(company.description)),
        ("recruiter role or title", bool(membership and present(membership.designation))),
    ]
    return _completion(required)


def ensure_company_ready_to_post(company: CompanyProfile, membership: RecruiterCompanyMember | None = None) -> CompletionResult:
    result = check_company_profile_completion(company, membership)
    if not result.is_complete:
        missing = ", ".join(result.missing_fields[:8])
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Complete company profile before posting jobs. Missing: {missing}.",
        )
    return result


def normalize_domain(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url if "://" in url else f"https://{url}")
    host = (parsed.netloc or parsed.path).split("/", 1)[0].lower()
    if host.startswith("www."):
        host = host[4:]
    return host or None


def validate_http_url(url: str | None, field_name: str) -> None:
    if not url:
        return
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{field_name} must be a valid http or https URL.")


def validate_job_career_link(company: CompanyProfile, url: str) -> CareerLinkResult:
    validate_http_url(url, "Career page URL")
    job_domain = normalize_domain(url)
    company_domain = normalize_domain(company.website)
    if company_domain and job_domain and (job_domain == company_domain or job_domain.endswith(f".{company_domain}")):
        return CareerLinkResult(JobCareerLinkStatus.LINK_MATCHED_COMPANY_DOMAIN.value)
    if job_domain and any(job_domain == domain or job_domain.endswith(f".{domain}") for domain in KNOWN_ATS_DOMAINS):
        return CareerLinkResult(JobCareerLinkStatus.LINK_EXTERNAL_ATS.value)
    return CareerLinkResult(
        JobCareerLinkStatus.LINK_SUSPICIOUS.value,
        "This career link does not match the company website domain. Admin review recommended.",
    )
