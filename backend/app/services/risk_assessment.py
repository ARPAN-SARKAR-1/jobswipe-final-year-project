import json
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.candidate_risk_assessment import CandidateRiskAssessment
from app.models.company import Company
from app.models.company_member import CompanyMember
from app.models.enums import (
    CompanyVerificationStatus,
    JobModerationStatus,
    RecruiterVerificationStatus,
    RiskAutoAction,
    RiskLevel,
)
from app.models.job import Job
from app.models.job_risk_assessment import JobRiskAssessment
from app.models.job_seeker_profile import JobSeekerProfile
from app.models.recruiter_profile import RecruiterProfile
from app.models.report import Report
from app.models.user import User
from app.services.company_claims import reserved_brand_match
from app.services.notifications import notify_admins

MONEY_REQUEST_KEYWORDS = [
    "registration fee",
    "pay registration fee",
    "joining fee",
    "pay joining fee",
    "security deposit",
    "refundable amount",
    "training fee",
    "send money",
    "upi",
    "payment before joining",
    "whatsapp only",
]
EARLY_DOCUMENT_KEYWORDS = ["aadhaar", "pan card", "passport copy", "bank details", "otp"]


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def risk_level(score: int) -> str:
    if score >= 81:
        return RiskLevel.CRITICAL.value
    if score >= 61:
        return RiskLevel.HIGH.value
    if score >= 31:
        return RiskLevel.MEDIUM.value
    return RiskLevel.LOW.value


def salary_numbers(value: str | None) -> list[float]:
    if not value:
        return []
    cleaned = value.replace(",", "")
    return [float(match) for match in re.findall(r"\d+(?:\.\d+)?", cleaned)]


def assess_job_risk(db: Session, job: Job) -> JobRiskAssessment:
    score = 0
    reasons: list[str] = []
    text = f"{job.title} {job.description} {job.eligibility or ''} {job.salary or ''}".lower()
    for keyword in MONEY_REQUEST_KEYWORDS:
        if keyword in text:
            score += 35 if keyword not in {"upi", "whatsapp only"} else 20
            reasons.append(f"Job content contains money-request signal: {keyword}.")
    for keyword in EARLY_DOCUMENT_KEYWORDS:
        if keyword in text:
            score += 12
            reasons.append(f"Job asks for sensitive documents early: {keyword}.")

    if job.required_experience_level.lower().startswith("fresher"):
        high_salary = any(number >= 1800000 for number in salary_numbers(job.salary))
        if high_salary:
            score += 20
            reasons.append("Salary appears unusually high for fresher role.")

    company = job.company or (db.get(Company, job.company_id) if job.company_id else None)
    profile = db.scalar(select(RecruiterProfile).where(RecruiterProfile.user_id == job.recruiter_id))
    recruiter = job.recruiter or db.get(User, job.recruiter_id)
    member = (
        db.scalar(
            select(CompanyMember)
            .where(CompanyMember.company_id == job.company_id)
            .where(CompanyMember.user_id == job.recruiter_id)
        )
        if job.company_id
        else None
    )
    if company is None or company.verification_status != CompanyVerificationStatus.VERIFIED.value:
        score += 30
        reasons.append("Company is not verified.")
    if profile is None or profile.recruiter_verification_status != RecruiterVerificationStatus.VERIFIED.value:
        score += 25
        reasons.append("Recruiter profile is not verified.")
    if member is None or member.verification_status != RecruiterVerificationStatus.VERIFIED.value:
        score += 25
        reasons.append("Recruiter is not a verified company member.")
    if company and profile and profile.company_id != company.id:
        score += 35
        reasons.append("Recruiter-company relation does not match the job company.")
    if company and company.official_email_domain and profile and profile.official_email:
        recruiter_domain = profile.official_email.rsplit("@", 1)[-1].lower() if "@" in profile.official_email else ""
        if recruiter_domain and recruiter_domain != company.official_email_domain:
            score += 20
            reasons.append("Recruiter official email domain does not match company domain.")
    match_name, _match_score = reserved_brand_match(job.company_name)
    if match_name and (company is None or company.verification_status != CompanyVerificationStatus.VERIFIED.value):
        score += 35
        reasons.append(f"Company name resembles reserved brand {match_name} but is not verified.")
    recent_cutoff = utc_now_naive() - timedelta(days=7)
    recent_jobs = db.scalar(
        select(func.count(Job.id)).where(Job.recruiter_id == job.recruiter_id).where(Job.created_at >= recent_cutoff)
    ) or 0
    if recent_jobs >= 5:
        score += 15
        reasons.append("New or active recruiter has posted many jobs recently.")
    duplicate_jobs = db.scalar(
        select(func.count(Job.id))
        .where(Job.recruiter_id == job.recruiter_id)
        .where(Job.title == job.title)
        .where(Job.id != job.id)
    ) or 0
    if duplicate_jobs >= 2:
        score += 15
        reasons.append("Duplicate job spam pattern detected.")
    recruiter_reports = db.scalar(select(func.count(Report.id)).where(Report.recruiter_id == job.recruiter_id)) or 0
    if recruiter_reports >= 3:
        score += 20
        reasons.append("Recruiter has repeated reports.")
    if recruiter and recruiter.created_at and recruiter.created_at >= recent_cutoff and recent_jobs >= 3:
        score += 15
        reasons.append("Newly created recruiter is posting multiple jobs quickly.")

    final_score = min(score, 100)
    final_level = risk_level(final_score)
    auto_action = RiskAutoAction.NONE.value
    if final_level == RiskLevel.MEDIUM.value:
        auto_action = RiskAutoAction.FLAGGED.value
    elif final_level in {RiskLevel.HIGH.value, RiskLevel.CRITICAL.value}:
        auto_action = RiskAutoAction.PAUSED.value if final_level == RiskLevel.CRITICAL.value else RiskAutoAction.FLAGGED.value
        job.moderation_status = JobModerationStatus.PAUSED.value
        job.moderation_reason = "Job is under safety review."

    assessment = db.scalar(select(JobRiskAssessment).where(JobRiskAssessment.job_id == job.id))
    if assessment is None:
        assessment = JobRiskAssessment(job_id=job.id)
        db.add(assessment)
    assessment.risk_score = final_score
    assessment.risk_level = final_level
    assessment.reasons = json.dumps(reasons)
    assessment.auto_action = auto_action
    if final_level in {RiskLevel.HIGH.value, RiskLevel.CRITICAL.value}:
        notify_admins(
            db,
            "Suspicious job flagged",
            f"{job.title} was flagged by rule-based safety checks.",
            "JOB_RISK_FLAGGED",
            "/admin/dashboard",
        )
    return assessment


def assess_candidate_risk(db: Session, job_seeker: User, reason: str | None = None) -> CandidateRiskAssessment:
    score = 20
    reasons: list[str] = []
    if reason:
        score += 25
        reasons.append(f"Recruiter report: {reason}")
    profile = db.scalar(select(JobSeekerProfile).where(JobSeekerProfile.user_id == job_seeker.id))
    if profile is None or not profile.resume_pdf_url or not profile.skills or not profile.education:
        score += 20
        reasons.append("Candidate profile has missing key details.")
    if profile and profile.github_url and "github.com" not in profile.github_url.lower():
        score += 15
        reasons.append("GitHub URL does not point to github.com.")
    applications = db.scalar(select(func.count(Application.id)).where(Application.job_seeker_id == job_seeker.id)) or 0
    if applications >= 20:
        score += 20
        reasons.append("Candidate has unusually high application volume.")
    if any(part in job_seeker.email.lower() for part in ["fake", "test", "spam"]):
        score += 15
        reasons.append("Email pattern looks suspicious.")
    if profile and profile.phone:
        duplicate_phone = db.scalar(
            select(func.count(JobSeekerProfile.id))
            .where(JobSeekerProfile.phone == profile.phone)
            .where(JobSeekerProfile.user_id != job_seeker.id)
        ) or 0
        if duplicate_phone:
            score += 20
            reasons.append("Phone number is reused by another account.")

    final_score = min(score, 100)
    assessment = db.scalar(select(CandidateRiskAssessment).where(CandidateRiskAssessment.job_seeker_id == job_seeker.id))
    if assessment is None:
        assessment = CandidateRiskAssessment(job_seeker_id=job_seeker.id)
        db.add(assessment)
    existing = []
    if assessment.reasons:
        try:
            existing = json.loads(assessment.reasons)
        except json.JSONDecodeError:
            existing = [assessment.reasons]
    merged = [*existing, *[item for item in reasons if item not in existing]]
    assessment.risk_score = max(assessment.risk_score or 0, final_score)
    assessment.risk_level = risk_level(assessment.risk_score)
    assessment.reasons = json.dumps(merged)
    notify_admins(
        db,
        "Suspicious candidate reported",
        f"{job_seeker.name} was reported for admin review.",
        "CANDIDATE_RISK_FLAGGED",
        "/admin/dashboard",
    )
    return assessment
