from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.application import Application
from app.models.application_timeline import ApplicationTimeline
from app.models.candidate_risk_assessment import CandidateRiskAssessment
from app.models.chat_message import ChatMessage
from app.models.chat_thread import ChatThread
from app.models.company import Company
from app.models.company_claim_request import CompanyClaimRequest
from app.models.company_member import CompanyMember
from app.models.company_profile import CompanyProfile
from app.models.company_review import CompanyReview
from app.models.enums import (
    ApplicationStatus,
    ChatThreadStatus,
    CompanyClaimStatus,
    CompanyMemberRole,
    CompanyVerificationStatus,
    JobModerationStatus,
    RecruiterVerificationStatus,
    ReportStatus,
    ReportType,
    ReviewModerationStatus,
    SwipeAction,
    UserRole,
)
from app.models.job import Job
from app.models.job_seeker_profile import JobSeekerProfile
from app.models.notification import Notification
from app.models.recruiter_profile import RecruiterProfile
from app.models.recruiter_review import RecruiterReview
from app.models.report import Report
from app.models.security_settings import SecuritySettings
from app.models.swipe import Swipe
from app.models.user import User
from app.services.company_claims import assess_company_claim_risk, claim_risk_reasons_json, hash_verification_token
from app.services.company_reviews import recalculate_company_rating
from app.services.recruiter_reviews import recalculate_recruiter_rating
from app.services.risk_assessment import assess_candidate_risk, assess_job_risk
from app.services.user_risk_assessment import update_user_risk


def now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_or_create_user(db, name: str, email: str, password: str, role: UserRole) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role=role.value,
            accepted_terms=True,
            accepted_terms_at=now_naive(),
            accepted_privacy=True,
            accepted_privacy_at=now_naive(),
            account_status="ACTIVE",
        )
        db.add(user)
        db.flush()
    user.name = name
    user.password_hash = hash_password(password)
    user.role = role.value
    user.accepted_terms = True
    user.accepted_terms_at = user.accepted_terms_at or now_naive()
    user.accepted_privacy = True
    user.accepted_privacy_at = user.accepted_privacy_at or now_naive()
    user.account_status = "ACTIVE"
    user.suspension_reason = None
    return user


def get_or_create_company(db, name: str, **values) -> Company:
    company = db.scalar(select(Company).where(Company.company_name == name))
    if company is None:
        company = Company(company_name=name)
        db.add(company)
        db.flush()
    for key, value in values.items():
        setattr(company, key, value)
    return company


def ensure_legacy_company_profile(db, recruiter: User, company: Company) -> None:
    legacy = db.scalar(select(CompanyProfile).where(CompanyProfile.recruiter_id == recruiter.id))
    if legacy is None:
        legacy = CompanyProfile(recruiter_id=recruiter.id)
        db.add(legacy)
    legacy.company_name = company.company_name
    legacy.website = company.website
    legacy.location = company.headquarters_location
    legacy.description = company.description


def configure_recruiter(
    db,
    recruiter: User,
    company: Company,
    admin: User,
    company_role: str,
    verification_status: str,
    note: str,
    designation: str = "Talent Partner",
) -> None:
    profile = db.scalar(select(RecruiterProfile).where(RecruiterProfile.user_id == recruiter.id))
    if profile is None:
        profile = RecruiterProfile(user_id=recruiter.id)
        db.add(profile)
    profile.company_id = company.id
    profile.official_email = profile.official_email or recruiter.email
    profile.designation = designation
    profile.department = "Hiring"
    profile.recruiter_verification_status = verification_status
    profile.verification_note = note
    profile.verified_at = now_naive() if verification_status == RecruiterVerificationStatus.VERIFIED.value else None
    profile.verified_by_admin_id = admin.id if verification_status == RecruiterVerificationStatus.VERIFIED.value else None

    member = db.scalar(
        select(CompanyMember).where(CompanyMember.company_id == company.id).where(CompanyMember.user_id == recruiter.id)
    )
    if member is None:
        member = CompanyMember(company_id=company.id, user_id=recruiter.id, requested_at=now_naive())
        db.add(member)
    member.company_role = company_role
    member.verification_status = verification_status
    member.verified_at = now_naive() if verification_status == RecruiterVerificationStatus.VERIFIED.value else None
    member.verified_by_user_id = admin.id if verification_status == RecruiterVerificationStatus.VERIFIED.value else None
    member.note = note

    if company_role == CompanyMemberRole.COMPANY_OWNER.value:
        ensure_legacy_company_profile(db, recruiter, company)


def ensure_profile(
    db,
    user: User,
    phone: str,
    github_url: str,
    education: str,
    degree: str,
    college: str,
    passing_year: int,
    cgpa_or_percentage: str,
    skills: str,
    experience_level: str,
    preferred_location: str,
    preferred_job_type: str,
) -> None:
    profile = db.scalar(select(JobSeekerProfile).where(JobSeekerProfile.user_id == user.id))
    if profile is None:
        profile = JobSeekerProfile(user_id=user.id)
        db.add(profile)
    profile.phone = phone
    profile.github_url = github_url
    profile.education = education
    profile.degree = degree
    profile.college = college
    profile.passing_year = passing_year
    profile.cgpa_or_percentage = cgpa_or_percentage
    profile.skills = skills
    profile.experience_level = experience_level
    profile.preferred_location = preferred_location
    profile.preferred_job_type = preferred_job_type


def ensure_job(db, recruiter: User, company: Company, title: str, **values) -> Job:
    job = db.scalar(select(Job).where(Job.title == title))
    if job is None:
        job = Job(recruiter_id=recruiter.id, title=title)
        db.add(job)
    job.recruiter_id = recruiter.id
    job.company_id = company.id
    job.company_name = company.company_name
    job.company_logo_url = company.company_logo_url
    for key, value in values.items():
        setattr(job, key, value)
    return job


def ensure_application(db, seeker: User, job: Job, status_value: str) -> Application:
    application = db.scalar(select(Application).where(Application.job_seeker_id == seeker.id).where(Application.job_id == job.id))
    if application is None:
        profile = db.scalar(select(JobSeekerProfile).where(JobSeekerProfile.user_id == seeker.id))
        application = Application(
            job_seeker_id=seeker.id,
            job_id=job.id,
            resume_pdf_url=profile.resume_pdf_url if profile else None,
            github_url=profile.github_url if profile else None,
            status=status_value,
        )
        db.add(application)
        db.flush()
    application.status = status_value
    if db.scalar(select(ApplicationTimeline).where(ApplicationTimeline.application_id == application.id).limit(1)) is None:
        db.add(
            ApplicationTimeline(
                application_id=application.id,
                action=status_value,
                old_status=None,
                new_status=status_value,
                note=f"Seed timeline event for {status_value.lower()} application.",
                created_by_user_id=seeker.id,
            )
        )
    return application


def ensure_notification(db, user: User, title: str, message: str, notification_type: str, link_url: str) -> None:
    exists = db.scalar(
        select(Notification).where(Notification.user_id == user.id).where(Notification.title == title).where(Notification.type == notification_type)
    )
    if exists is None:
        db.add(Notification(user_id=user.id, title=title, message=message, type=notification_type, link_url=link_url))


def ensure_report(db, reporter: User, job: Job, report_type: str, description: str) -> None:
    exists = db.scalar(select(Report).where(Report.reporter_id == reporter.id).where(Report.job_id == job.id).where(Report.report_type == report_type))
    if exists is None:
        db.add(
            Report(
                reporter_id=reporter.id,
                job_id=job.id,
                recruiter_id=job.recruiter_id,
                report_type=report_type,
                description=description,
                status=ReportStatus.PENDING.value,
            )
        )


def ensure_review(
    db,
    seeker: User,
    company: Company,
    rating: int,
    text: str,
    title: str,
    pros: str,
    cons: str | None = None,
    moderation_status: str = ReviewModerationStatus.VISIBLE.value,
) -> None:
    exists = db.scalar(select(CompanyReview).where(CompanyReview.company_id == company.id).where(CompanyReview.job_seeker_id == seeker.id))
    if exists is None:
        application_id = db.scalar(
            select(Application.id)
            .join(Job, Application.job_id == Job.id)
            .where(Application.job_seeker_id == seeker.id)
            .where(Job.company_id == company.id)
            .order_by(Application.created_at.desc(), Application.id.desc())
            .limit(1)
        )
        exists = CompanyReview(company_id=company.id, job_seeker_id=seeker.id)
        db.add(exists)
        exists.application_id = application_id
    exists.rating = rating
    exists.overall_rating = rating
    exists.work_culture_rating = rating
    exists.interview_process_rating = max(1, min(5, rating - 1 if rating > 3 else rating))
    exists.salary_transparency_rating = max(1, min(5, rating))
    exists.growth_opportunity_rating = max(1, min(5, rating))
    exists.review_title = title
    exists.review_text = text
    exists.pros = pros
    exists.cons = cons
    exists.is_anonymous = False
    exists.moderation_status = moderation_status
    exists.is_visible = moderation_status == ReviewModerationStatus.VISIBLE.value
    db.flush()
    recalculate_company_rating(db, company.id)


def ensure_recruiter_review(
    db,
    seeker: User,
    recruiter: User,
    application: Application,
    rating: int,
    title: str,
    text: str,
    moderation_status: str = ReviewModerationStatus.VISIBLE.value,
) -> None:
    exists = db.scalar(
        select(RecruiterReview)
        .where(RecruiterReview.recruiter_id == recruiter.id)
        .where(RecruiterReview.job_seeker_id == seeker.id)
    )
    if exists is None:
        exists = RecruiterReview(recruiter_id=recruiter.id, job_seeker_id=seeker.id, application_id=application.id)
        db.add(exists)
    exists.application_id = application.id
    exists.overall_rating = rating
    exists.communication_rating = rating
    exists.response_time_rating = max(1, min(5, rating - 1 if rating > 3 else rating))
    exists.professionalism_rating = rating
    exists.transparency_rating = max(1, min(5, rating))
    exists.review_title = title
    exists.review_text = text
    exists.is_anonymous = False
    exists.moderation_status = moderation_status
    exists.is_visible = moderation_status == ReviewModerationStatus.VISIBLE.value
    db.flush()
    recalculate_recruiter_rating(db, recruiter.id)


def ensure_claim(
    db,
    company: Company,
    requester: User,
    requested_name: str,
    domain: str,
    official_email: str,
    claim_status: str,
    admin: User,
    email_verified: bool,
    admin_note: str | None,
) -> None:
    claim = db.scalar(
        select(CompanyClaimRequest)
        .where(CompanyClaimRequest.requested_company_name == requested_name)
        .where(CompanyClaimRequest.requester_user_id == requester.id)
    )
    if claim is None:
        claim = CompanyClaimRequest(
            company_id=company.id,
            requested_company_name=requested_name,
            requested_domain=domain,
            requester_user_id=requester.id,
            official_email=official_email,
        )
        db.add(claim)
        db.flush()
    risk_score, risk_level, reasons = assess_company_claim_risk(requested_name, domain, official_email)
    claim.company_id = company.id
    claim.requested_domain = domain
    claim.official_email = official_email
    claim.claim_status = claim_status
    claim.risk_score = risk_score
    claim.risk_level = risk_level
    claim.requires_admin_review = risk_score >= 61
    claim.risk_reasons = claim_risk_reasons_json(reasons)
    claim.email_verified_at = now_naive() if email_verified else None
    claim.reviewed_by_admin_id = admin.id if claim_status in {CompanyClaimStatus.VERIFIED.value, CompanyClaimStatus.REJECTED.value} else None
    claim.admin_note = admin_note
    if claim_status == CompanyClaimStatus.PENDING.value:
        claim.verification_token_hash = hash_verification_token("demo-company-claim-token")
        claim.token_expires_at = now_naive() + timedelta(hours=24)
    else:
        claim.verification_token_hash = None
        claim.token_expires_at = None


def main() -> None:
    db = SessionLocal()
    try:
        owner = get_or_create_user(db, "Owner User", "owner@jobswipe.dev", "Owner@123", UserRole.OWNER)
        owner.is_protected_owner = True
        admin = get_or_create_user(db, "Admin User", "admin@jobswipe.dev", "Admin@123", UserRole.ADMIN)
        admin.is_protected_owner = False
        security_settings = db.get(SecuritySettings, 1)
        if security_settings is None:
            security_settings = SecuritySettings(id=1)
            db.add(security_settings)
        security_settings.captcha_login_enabled = True
        security_settings.captcha_signup_enabled = True
        security_settings.captcha_forgot_password_enabled = True
        security_settings.captcha_reports_enabled = False
        security_settings.captcha_company_claims_enabled = False

        seeker = get_or_create_user(db, "Aarav Sharma", "jobseeker@jobswipe.dev", "Jobseeker@123", UserRole.JOB_SEEKER)
        seeker_two = get_or_create_user(db, "Meera Iyer", "meera@jobswipe.dev", "Jobseeker@123", UserRole.JOB_SEEKER)
        seeker_three = get_or_create_user(db, "Ravi Demo", "ravi.demo@jobswipe.dev", "Jobseeker@123", UserRole.JOB_SEEKER)

        recruiter = get_or_create_user(db, "Neha Recruiter", "recruiter@jobswipe.dev", "Recruiter@123", UserRole.RECRUITER)
        recruiter_two = get_or_create_user(db, "Rohan Hiring", "rohan@jobswipe.dev", "Recruiter@123", UserRole.RECRUITER)
        recruiter_three = get_or_create_user(db, "Anika Talent", "anika@jobswipe.dev", "Recruiter@123", UserRole.RECRUITER)
        recruiter_four = get_or_create_user(db, "Vivek Campus", "vivek@jobswipe.dev", "Recruiter@123", UserRole.RECRUITER)
        recruiter_five = get_or_create_user(db, "Priya Analytics", "priya@jobswipe.dev", "Recruiter@123", UserRole.RECRUITER)
        pending_recruiter = get_or_create_user(db, "Pending Join Recruiter", "pending.join@jobswipe.dev", "Recruiter@123", UserRole.RECRUITER)
        orbit_recruiter = get_or_create_user(db, "Orbit Pending Recruiter", "orbit@jobswipe.dev", "Recruiter@123", UserRole.RECRUITER)
        risky_requester = get_or_create_user(db, "Risky Claim Recruiter", "risky.claim@jobswipe.dev", "Recruiter@123", UserRole.RECRUITER)

        ensure_profile(
            db,
            seeker,
            "+91 98765 43210",
            "https://github.com/jobswipe-demo",
            "Bachelor of Technology",
            "Computer Science",
            "City Engineering College",
            2026,
            "8.4 CGPA",
            "Python, SQL, React, Testing",
            "Fresher",
            "Bengaluru",
            "Full-time",
        )
        ensure_profile(
            db,
            seeker_two,
            "+91 91234 56789",
            "https://github.com/meera-demo",
            "Bachelor of Science",
            "Data Science",
            "National Institute of Technology",
            2025,
            "82%",
            "Data Science, Machine Learning, Python, SQL",
            "0-1 years",
            "Remote",
            "Internship",
        )
        ensure_profile(
            db,
            seeker_three,
            "+91 90000 00000",
            "https://portfolio.invalid/ravi",
            "Bachelor of Computer Applications",
            "Computer Applications",
            "Metro College",
            2026,
            "7.1 CGPA",
            "React, SQL",
            "Fresher",
            "Kolkata",
            "Internship",
        )

        verified_companies = [
            (
                "NovaWorks Labs",
                "Product-based",
                "Software Products",
                "https://novaworks.example",
                "novaworks.example",
                "Bengaluru",
                "Product engineering studio hiring fresh talent.",
                recruiter,
                CompanyMemberRole.COMPANY_OWNER.value,
            ),
            (
                "CloudNest Systems",
                "Service-based",
                "Cloud Consulting",
                "https://cloudnest.example",
                "cloudnest.example",
                "Hyderabad",
                "Cloud and data consultancy for fast-growing teams.",
                recruiter_two,
                CompanyMemberRole.COMPANY_OWNER.value,
            ),
            (
                "SkillBridge Technologies",
                "Startup",
                "EdTech",
                "https://skillbridge.example",
                "skillbridge.example",
                "Pune",
                "Early-career training and internship platform.",
                recruiter_three,
                CompanyMemberRole.COMPANY_OWNER.value,
            ),
            (
                "FreshKart Digital",
                "Product-based",
                "Commerce Technology",
                "https://freshkart.example",
                "freshkart.example",
                "Mumbai",
                "Digital commerce platform with fresher engineering roles.",
                recruiter_four,
                CompanyMemberRole.COMPANY_OWNER.value,
            ),
            (
                "CampusForge Analytics",
                "Consultancy",
                "Data Analytics",
                "https://campusforge.example",
                "campusforge.example",
                "Gurugram",
                "Analytics consultancy with campus hiring programs.",
                recruiter_five,
                CompanyMemberRole.COMPANY_OWNER.value,
            ),
        ]

        company_by_name: dict[str, Company] = {}
        for name, company_type, industry, website, domain, location, description, company_owner, role in verified_companies:
            company = get_or_create_company(
                db,
                name,
                company_type=company_type,
                industry=industry,
                website=website,
                official_email_domain=domain,
                headquarters_location=location,
                description=description,
                verification_status=CompanyVerificationStatus.VERIFIED.value,
                verification_note="Verified seed company for cold-start demo.",
                verified_at=now_naive(),
                verified_by_admin_id=admin.id,
            )
            company_by_name[name] = company
            configure_recruiter(
                db,
                company_owner,
                company,
                admin,
                role,
                RecruiterVerificationStatus.VERIFIED.value,
                "Verified seed recruiter for demo.",
            )

        configure_recruiter(
            db,
            pending_recruiter,
            company_by_name["NovaWorks Labs"],
            admin,
            CompanyMemberRole.COMPANY_RECRUITER.value,
            RecruiterVerificationStatus.PENDING.value,
            "Pending join request seeded for admin/company-owner demo.",
            "Campus Recruiter",
        )
        configure_recruiter(
            db,
            recruiter_four,
            company_by_name["FreshKart Digital"],
            admin,
            CompanyMemberRole.COMPANY_ADMIN.value,
            RecruiterVerificationStatus.VERIFIED.value,
            "Verified company admin recruiter for demo.",
            "Company Hiring Admin",
        )

        pending_company = get_or_create_company(
            db,
            "OrbitHire Ventures",
            company_type="Startup",
            industry="Recruitment Technology",
            website="https://orbithire.example",
            official_email_domain="orbithire.example",
            headquarters_location="Kolkata",
            description="Pending company used for verification demo.",
            verification_status=CompanyVerificationStatus.PENDING.value,
            verification_note="Pending seed company for verification demo.",
            verified_at=None,
            verified_by_admin_id=None,
        )
        configure_recruiter(
            db,
            orbit_recruiter,
            pending_company,
            admin,
            CompanyMemberRole.COMPANY_OWNER.value,
            RecruiterVerificationStatus.PENDING.value,
            "Pending seed recruiter under pending company.",
        )

        rejected_company = get_or_create_company(
            db,
            "Infosys Careers Demo",
            company_type="MNC",
            industry="Information Technology",
            website="https://infosys-careers.example",
            official_email_domain="infosys-careers.example",
            headquarters_location="Bengaluru",
            description="Rejected high-risk seed company used to demonstrate impersonation protection.",
            verification_status=CompanyVerificationStatus.REJECTED.value,
            verification_note="Rejected because the name resembles a reserved brand in the demo dataset.",
            verified_at=None,
            verified_by_admin_id=admin.id,
        )
        configure_recruiter(
            db,
            risky_requester,
            rejected_company,
            admin,
            CompanyMemberRole.COMPANY_OWNER.value,
            RecruiterVerificationStatus.REJECTED.value,
            "Rejected seed recruiter for high-risk company claim demo.",
        )

        db.flush()
        ensure_claim(
            db,
            rejected_company,
            risky_requester,
            "Infosys Careers Demo",
            "infosys-careers.example",
            "hr@infosys-careers.example",
            CompanyClaimStatus.REJECTED.value,
            admin,
            True,
            "Rejected because the company name is similar to a reserved brand.",
        )
        pending_claim_company = get_or_create_company(
            db,
            "TCS Hiring Desk Demo",
            company_type="MNC",
            industry="Information Technology",
            website="https://tcs-demo.example",
            official_email_domain="tcs.com",
            headquarters_location="Mumbai",
            description="Pending high-risk claim used to demonstrate Owner/Admin review.",
            verification_status=CompanyVerificationStatus.PENDING.value,
            verification_note="Official domain simulated; awaiting Owner/Admin review.",
        )
        ensure_claim(
            db,
            pending_claim_company,
            pending_recruiter,
            "TCS Hiring Desk Demo",
            "tcs.com",
            "hr@tcs.com",
            CompanyClaimStatus.PENDING.value,
            admin,
            True,
            "Official email simulated for final year demo; Owner/Admin review required.",
        )

        db.flush()
        deadline = date.today() + timedelta(days=30)
        safe_jobs = [
            (
                recruiter,
                company_by_name["NovaWorks Labs"],
                "Junior Java Developer",
                "Java, SQL, Testing",
                "Full-time",
                "On-site",
                "Fresher",
                "Bengaluru",
                "INR 4 LPA - INR 7 LPA",
                False,
                None,
                None,
            ),
            (
                recruiter,
                company_by_name["NovaWorks Labs"],
                "Python Backend Intern",
                "Python, SQL, Cloud",
                "Internship",
                "Hybrid",
                "Fresher",
                "Pune",
                "INR 15,000 - INR 30,000 / month",
                False,
                None,
                None,
            ),
            (
                recruiter_two,
                company_by_name["CloudNest Systems"],
                "Cloud Support Engineer",
                "Cloud, SQL, Testing",
                "Full-time",
                "Hybrid",
                "0-1 years",
                "Chennai",
                "INR 5 LPA - INR 8 LPA",
                True,
                1.0,
                "One-year service agreement for cloud certification sponsorship.",
            ),
            (
                recruiter_three,
                company_by_name["SkillBridge Technologies"],
                "Data Science Intern",
                "Data Science, Python, Machine Learning",
                "Internship",
                "Hybrid",
                "Fresher",
                "Hyderabad",
                "INR 18,000 - INR 32,000 / month",
                False,
                None,
                None,
            ),
            (
                recruiter_four,
                company_by_name["FreshKart Digital"],
                "React Frontend Associate",
                "React, UI/UX, Testing",
                "Full-time",
                "Remote",
                "0-1 years",
                "Remote",
                "INR 4 LPA - INR 6 LPA",
                False,
                None,
                None,
            ),
            (
                recruiter_five,
                company_by_name["CampusForge Analytics"],
                "SQL Data Analyst",
                "SQL, Data Science, Python",
                "Full-time",
                "On-site",
                "0-1 years",
                "Gurugram",
                "INR 4.5 LPA - INR 7 LPA",
                True,
                1.0,
                "One-year bond for candidates receiving analytics bootcamp sponsorship.",
            ),
        ]
        jobs: list[Job] = []
        for index, (job_recruiter, company, title, skills, job_type, work_mode, exp, location, salary, has_bond, bond_years, bond_details) in enumerate(safe_jobs):
            job = ensure_job(
                db,
                job_recruiter,
                company,
                title,
                location=location,
                job_type=job_type,
                work_mode=work_mode,
                salary=salary,
                required_skills=skills,
                required_experience_level=exp,
                description="Work with a supportive team on real product problems and build portfolio-ready experience.",
                eligibility="Freshers and early-career candidates with strong fundamentals may apply.",
                deadline=deadline + timedelta(days=index),
                is_active=True,
                has_bond=has_bond,
                bond_years=bond_years,
                bond_details=bond_details,
                moderation_status=JobModerationStatus.ACTIVE.value,
                moderation_reason=None,
            )
            jobs.append(job)

        risky_job = ensure_job(
            db,
            recruiter,
            company_by_name["NovaWorks Labs"],
            "Urgent Fresher Joining Fee Offer",
            location="Remote",
            job_type="Full-time",
            work_mode="Remote",
            salary="INR 25 LPA",
            required_skills="Python, SQL",
            required_experience_level="Fresher",
            description="Payment before joining is required. Pay joining fee and security deposit by UPI. WhatsApp only. Aadhaar and bank details required before interview.",
            eligibility="Freshers may apply immediately.",
            deadline=deadline + timedelta(days=10),
            is_active=True,
            has_bond=False,
            bond_years=None,
            bond_details=None,
            moderation_status=JobModerationStatus.ACTIVE.value,
            moderation_reason=None,
        )
        jobs.append(risky_job)

        db.flush()
        for job in jobs:
            assess_job_risk(db, job)
        db.flush()

        app_one = ensure_application(db, seeker, jobs[0], ApplicationStatus.APPLIED.value)
        app_two = ensure_application(db, seeker, jobs[1], ApplicationStatus.VIEWED.value)
        app_three = ensure_application(db, seeker_two, jobs[2], ApplicationStatus.SHORTLISTED.value)
        ensure_application(db, seeker_three, jobs[3], ApplicationStatus.APPLIED.value)

        if db.scalar(select(Swipe).where(Swipe.job_seeker_id == seeker.id).where(Swipe.job_id == jobs[0].id)) is None:
            db.add(Swipe(job_seeker_id=seeker.id, job_id=jobs[0].id, action=SwipeAction.LIKE.value))
        if db.scalar(select(Swipe).where(Swipe.job_seeker_id == seeker.id).where(Swipe.job_id == jobs[3].id)) is None:
            db.add(Swipe(job_seeker_id=seeker.id, job_id=jobs[3].id, action=SwipeAction.SAVE.value))
        if db.scalar(select(Swipe).where(Swipe.job_seeker_id == seeker_two.id).where(Swipe.job_id == jobs[4].id)) is None:
            db.add(Swipe(job_seeker_id=seeker_two.id, job_id=jobs[4].id, action=SwipeAction.REJECT.value))

        if db.scalar(select(ChatThread).where(ChatThread.application_id == app_three.id)) is None:
            chat_thread = ChatThread(
                application_id=app_three.id,
                recruiter_id=app_three.job.recruiter_id,
                job_seeker_id=app_three.job_seeker_id,
                job_id=app_three.job_id,
                status=ChatThreadStatus.ACTIVE.value,
                started_by_recruiter=True,
            )
            db.add(chat_thread)
            db.flush()
            db.add(
                ChatMessage(
                    thread_id=chat_thread.id,
                    sender_id=app_three.job.recruiter_id,
                    message_text="Hi, your profile has been shortlisted. Are you available for a quick discussion this week?",
                )
            )
            db.add(
                ChatMessage(
                    thread_id=chat_thread.id,
                    sender_id=app_three.job_seeker_id,
                    message_text="Thank you for shortlisting me. I am available and happy to discuss the role.",
                    is_read=True,
                )
            )
            db.add(
                ApplicationTimeline(
                    application_id=app_three.id,
                    action="CHAT_STARTED",
                    old_status=ApplicationStatus.SHORTLISTED.value,
                    new_status=ApplicationStatus.SHORTLISTED.value,
                    note="Seed recruiter-started chat.",
                    created_by_user_id=app_three.job.recruiter_id,
                )
            )

        ensure_review(
            db,
            seeker,
            company_by_name["NovaWorks Labs"],
            5,
            "Clear hiring process, transparent role details, and a fresher-friendly interview flow.",
            "Strong fresher hiring process",
            "Helpful communication and clear work culture expectations.",
            "Could share salary bands earlier.",
        )
        ensure_review(
            db,
            seeker_two,
            company_by_name["CloudNest Systems"],
            4,
            "Good role clarity and quick communication during the interview process.",
            "Responsive interview team",
            "Quick updates and practical interview questions.",
            "Salary details were shared after the first round.",
        )
        ensure_review(
            db,
            seeker_three,
            company_by_name["SkillBridge Technologies"],
            4,
            "Useful internship details for freshers and a supportive growth discussion.",
            "Good growth discussion",
            "The team explained learning goals well.",
            None,
        )
        ensure_review(
            db,
            seeker,
            company_by_name["SkillBridge Technologies"],
            2,
            "This review is hidden for moderation demo.",
            "Hidden moderation demo",
            "The company profile exists for testing moderation.",
            "Low transparency feedback hidden from public view.",
            ReviewModerationStatus.HIDDEN.value,
        )

        ensure_recruiter_review(
            db,
            seeker,
            app_one.job.recruiter,
            app_one,
            5,
            "Professional recruiter",
            "Communication was clear and the next steps were explained properly.",
        )
        ensure_recruiter_review(
            db,
            seeker,
            app_two.job.recruiter,
            app_two,
            4,
            "Quick response",
            "The recruiter responded quickly and shared interview expectations clearly.",
        )
        ensure_recruiter_review(
            db,
            seeker_two,
            app_three.job.recruiter,
            app_three,
            4,
            "Good shortlist communication",
            "The recruiter started the chat only after shortlisting and kept the discussion professional.",
        )

        ensure_report(
            db,
            seeker,
            risky_job,
            ReportType.ASKING_MONEY.value,
            "Seed report: job description asks candidates to pay a joining fee.",
        )
        ensure_report(
            db,
            seeker_two,
            jobs[0],
            ReportType.MISLEADING_INFO.value,
            "Seed report for admin moderation demonstration.",
        )

        assess_candidate_risk(db, seeker_three, "Recruiter reported suspicious portfolio URL and incomplete candidate details.")
        if db.scalar(select(CandidateRiskAssessment).where(CandidateRiskAssessment.job_seeker_id == seeker_three.id)):
            ensure_notification(
                db,
                admin,
                "Suspicious candidate reported",
                "A candidate risk item is waiting in the admin queue.",
                "CANDIDATE_RISK_FLAGGED",
                "/admin/dashboard",
            )

        ensure_notification(db, seeker, "Welcome to JobSwipe", "Complete your profile to improve job match scores.", "ADMIN_ACTION", "/jobseeker/profile")
        ensure_notification(db, recruiter, "Recruiter verified", "Your seed company and recruiter account are verified and can post jobs.", "RECRUITER_VERIFIED", "/recruiter/dashboard")
        ensure_notification(db, admin, "Company claim requires review", "A high-risk company claim is waiting for Owner/Admin review.", "COMPANY_CLAIM_REVIEW", "/admin/dashboard")
        ensure_notification(db, admin, "Suspicious job flagged", "A seeded job was paused by rule-based safety checks.", "JOB_RISK_FLAGGED", "/admin/dashboard")
        ensure_notification(db, pending_recruiter, "Company join request pending", "Your request to join NovaWorks Labs is waiting for approval.", "COMPANY_JOIN_REQUEST", "/recruiter/company")

        for seeded_user in [
            seeker,
            seeker_two,
            seeker_three,
            recruiter,
            recruiter_two,
            recruiter_three,
            recruiter_four,
            recruiter_five,
            pending_recruiter,
            orbit_recruiter,
            risky_requester,
        ]:
            update_user_risk(db, seeded_user)

        db.commit()
        _ = owner
        _ = app_one
        _ = app_two
        print("Seed data created or updated for cold-start demo.")
        print("Demo credentials:")
        print("owner@jobswipe.dev / Owner@123")
        print("admin@jobswipe.dev / Admin@123")
        print("jobseeker@jobswipe.dev / Jobseeker@123")
        print("recruiter@jobswipe.dev / Recruiter@123")
        print("Additional recruiters:")
        print("rohan@jobswipe.dev / Recruiter@123")
        print("pending.join@jobswipe.dev / Recruiter@123")
    finally:
        db.close()


if __name__ == "__main__":
    main()
