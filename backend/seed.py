import os
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.application import Application
from app.models.application_timeline import ApplicationTimeline
from app.models.chat_message import ChatMessage
from app.models.chat_thread import ChatThread
from app.models.company_profile import CompanyProfile
from app.models.enums import AccountStatus, ApplicationStatus, ChatThreadStatus, CompanyJoinStatus, CompanyType, CompanyVerificationStatus, RecruiterVerificationStatus, ReportStatus, ReportType, SwipeAction, UserRole
from app.models.job import Job
from app.models.job_seeker_profile import JobSeekerProfile
from app.models.notification import Notification
from app.models.report import Report
from app.models.recruiter_company_member import RecruiterCompanyMember
from app.models.swipe import Swipe
from app.models.user import User

TRUE_VALUES = {"1", "true", "yes", "y", "on"}


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def env_bool(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in TRUE_VALUES


def current_env() -> str:
    return (os.getenv("ENV") or "development").strip().lower()


def parse_email_list(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []
    emails: list[str] = []
    seen: set[str] = set()
    for item in raw_value.split(","):
        email = item.strip().lower()
        if not email or email in seen:
            continue
        if "@" not in email:
            raise RuntimeError(f"Invalid team account email: {email}")
        emails.append(email)
        seen.add(email)
    return emails


def name_from_email(email: str, role: UserRole) -> str:
    local_part = email.split("@", 1)[0].replace(".", " ").replace("_", " ").replace("-", " ")
    name = " ".join(part.capitalize() for part in local_part.split())
    return name or f"{role.value.title()} User"


def seed_team_account(db, email: str, role: UserRole, initial_password: str, reset_passwords: bool) -> str:
    now = utcnow()
    user = db.scalar(select(User).where(User.email == email))
    created = user is None
    if user is None:
        user = User(
            name=name_from_email(email, role),
            email=email,
            password_hash=hash_password(initial_password),
            role=role.value,
            accepted_terms=True,
            accepted_terms_at=now,
            accepted_privacy=True,
            accepted_privacy_at=now,
            account_status=AccountStatus.ACTIVE.value,
            email_verified=True,
            email_verified_at=now,
            is_protected_owner=role == UserRole.OWNER,
        )
        db.add(user)
        db.flush()
    else:
        if user.is_protected_owner and role != UserRole.OWNER:
            raise RuntimeError(f"Refusing to downgrade protected owner account: {email}")
        user.role = role.value
        user.account_status = AccountStatus.ACTIVE.value
        user.suspension_reason = None
        user.accepted_terms = True
        user.accepted_terms_at = user.accepted_terms_at or now
        user.accepted_privacy = True
        user.accepted_privacy_at = user.accepted_privacy_at or now
        user.email_verified = True
        user.email_verified_at = user.email_verified_at or now
        user.is_protected_owner = role == UserRole.OWNER
        if reset_passwords:
            user.password_hash = hash_password(initial_password)
    db.flush()
    role_label = "owner" if role == UserRole.OWNER else "admin"
    action = "created" if created else "verified"
    return f"Team {role_label} account {action}: {email}"


def seed_team_accounts_from_env(db) -> list[str]:
    owner_emails = parse_email_list(os.getenv("OWNER_EMAILS"))
    admin_emails = parse_email_list(os.getenv("ADMIN_EMAILS"))
    support_email = (os.getenv("SUPPORT_EMAIL") or "").strip().lower()
    initial_password = os.getenv("INITIAL_TEAM_PASSWORD") or ""
    reset_passwords = env_bool("RESET_TEAM_PASSWORDS", default=False)
    env = current_env()

    team_emails = set(owner_emails) | set(admin_emails)
    overlap = set(owner_emails) & set(admin_emails)
    if overlap:
        raise RuntimeError(f"Team account email cannot be both OWNER and ADMIN: {', '.join(sorted(overlap))}")
    if support_email and support_email in team_emails:
        raise RuntimeError("SUPPORT_EMAIL must not be listed as a login account in OWNER_EMAILS or ADMIN_EMAILS")
    if not team_emails:
        if env == "production":
            raise RuntimeError("OWNER_EMAILS or ADMIN_EMAILS is required to seed production team accounts.")
        return []
    if not initial_password:
        if env == "production":
            raise RuntimeError("INITIAL_TEAM_PASSWORD is required to seed owner/admin team accounts in production.")
        print("Team account import skipped: INITIAL_TEAM_PASSWORD is not set.")
        return []

    messages: list[str] = []
    for email in owner_emails:
        messages.append(seed_team_account(db, email, UserRole.OWNER, initial_password, reset_passwords))
    for email in admin_emails:
        messages.append(seed_team_account(db, email, UserRole.ADMIN, initial_password, reset_passwords))
    return messages


def get_or_create_user(db, name: str, email: str, password: str, role: UserRole) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user:
        user.role = role.value
        if user.account_status is None:
            user.account_status = "ACTIVE"
        user.email_verified = True
        user.email_verified_at = user.email_verified_at or utcnow()
        return user
    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role=role.value,
        accepted_terms=True,
        accepted_terms_at=utcnow(),
        accepted_privacy=True,
        accepted_privacy_at=utcnow(),
        account_status="ACTIVE",
        email_verified=True,
        email_verified_at=utcnow(),
    )
    db.add(user)
    db.flush()
    return user


def main() -> None:
    db = SessionLocal()
    try:
        team_account_messages = seed_team_accounts_from_env(db)
        if current_env() == "production":
            db.commit()
            for message in team_account_messages:
                print(message)
            print("Production team account seed completed.")
            return

        owner = get_or_create_user(db, "Owner User", "owner@jobswipe.dev", "Owner@123", UserRole.OWNER)
        owner.is_protected_owner = True
        owner.account_status = "ACTIVE"
        owner.suspension_reason = None
        owner.accepted_privacy = True
        owner.accepted_privacy_at = owner.accepted_privacy_at or utcnow()
        admin = get_or_create_user(db, "Admin User", "admin@jobswipe.dev", "Admin@123", UserRole.ADMIN)
        admin.is_protected_owner = False
        admin.account_status = "ACTIVE"
        admin.suspension_reason = None
        admin.accepted_privacy = True
        admin.accepted_privacy_at = admin.accepted_privacy_at or utcnow()
        seeker = get_or_create_user(db, "Aarav Sharma", "jobseeker@jobswipe.dev", "Jobseeker@123", UserRole.JOB_SEEKER)
        seeker_two = get_or_create_user(db, "Meera Iyer", "meera@jobswipe.dev", "Jobseeker@123", UserRole.JOB_SEEKER)
        recruiter = get_or_create_user(db, "Neha Recruiter", "recruiter@jobswipe.dev", "Recruiter@123", UserRole.RECRUITER)
        recruiter_two = get_or_create_user(db, "Rohan Hiring", "rohan@jobswipe.dev", "Recruiter@123", UserRole.RECRUITER)
        for seeded_user in [seeker, seeker_two, recruiter, recruiter_two]:
            seeded_user.accepted_privacy = True
            seeded_user.accepted_privacy_at = seeded_user.accepted_privacy_at or utcnow()
        db.flush()

        if not db.scalar(select(JobSeekerProfile).where(JobSeekerProfile.user_id == seeker.id)):
            db.add(
                JobSeekerProfile(
                    user_id=seeker.id,
                    phone="+91 98765 43210",
                    github_url="https://github.com/jobswipe-demo",
                    education="Bachelor of Technology",
                    degree="Computer Science",
                    college="City Engineering College",
                    passing_year=2026,
                    cgpa_or_percentage="8.4 CGPA",
                    skills="Python, SQL, React, Testing",
                    experience_level="Fresher",
                    preferred_location="Bengaluru",
                    preferred_job_type="Full-time",
                )
            )
        if not db.scalar(select(JobSeekerProfile).where(JobSeekerProfile.user_id == seeker_two.id)):
            db.add(
                JobSeekerProfile(
                    user_id=seeker_two.id,
                    phone="+91 91234 56789",
                    github_url="https://github.com/meera-demo",
                    education="Bachelor of Science",
                    degree="Data Science",
                    college="National Institute of Technology",
                    passing_year=2025,
                    cgpa_or_percentage="82%",
                    skills="Data Science, Machine Learning, Python, SQL",
                    experience_level="0-1 years",
                    preferred_location="Remote",
                    preferred_job_type="Internship",
                )
            )

        companies = [
            (recruiter, "NovaWorks Labs", "https://novaworks.example", "Bengaluru", "Product engineering studio hiring fresh talent.", "Software", CompanyType.STARTUP.value, "novaworks.example"),
            (recruiter_two, "CloudNest Systems", "https://cloudnest.example", "Hyderabad", "Cloud and data consultancy for fast-growing teams.", "Cloud consulting", CompanyType.CONSULTANCY.value, "cloudnest.example"),
        ]
        company_by_recruiter_id = {}
        for company_owner, name, website, location, description, industry, company_type, domain in companies:
            company = db.scalar(select(CompanyProfile).where(CompanyProfile.recruiter_id == company_owner.id))
            if company is None:
                company = CompanyProfile(
                    recruiter_id=company_owner.id,
                    company_name=name,
                    website=website,
                    location=location,
                    description=description,
                )
                db.add(company)
                db.flush()
            company.company_name = company.company_name or name
            company.website = company.website or website
            company.location = company.location or location
            company.description = company.description or description
            company.industry = company.industry or industry
            company.company_type = company.company_type or company_type
            company.official_email_domain = company.official_email_domain or domain
            company.verification_status = (
                CompanyVerificationStatus.VERIFIED.value
                if company_owner.id == recruiter.id
                else CompanyVerificationStatus.PENDING.value
            )
            company.recruiter_verification_status = (
                RecruiterVerificationStatus.VERIFIED.value
                if company_owner.id == recruiter.id
                else RecruiterVerificationStatus.PENDING.value
            )
            company.verification_note = (
                "Verified seed recruiter for demos."
                if company_owner.id == recruiter.id
                else "Pending seed recruiter for verification demos."
            )
            company.verified_at = (
                company.verified_at or utcnow()
                if company_owner.id == recruiter.id
                else None
            )
            company.verified_by_admin_id = admin.id if company_owner.id == recruiter.id else None
            membership = db.scalar(select(RecruiterCompanyMember).where(RecruiterCompanyMember.recruiter_id == company_owner.id))
            if membership is None:
                membership = RecruiterCompanyMember(recruiter_id=company_owner.id, company_id=company.id)
                db.add(membership)
            membership.company_id = company.id
            membership.designation = membership.designation or "Talent Partner"
            membership.work_email = membership.work_email or f"{company_owner.email.split('@', 1)[0]}@{domain}"
            membership.verification_status = company.recruiter_verification_status
            membership.company_join_status = (
                CompanyJoinStatus.APPROVED.value
                if company.recruiter_verification_status == RecruiterVerificationStatus.VERIFIED.value
                else CompanyJoinStatus.PENDING.value
            )
            membership.verified_at = company.verified_at
            membership.verified_by_admin_id = company.verified_by_admin_id
            membership.admin_note = company.verification_note
            company_by_recruiter_id[company_owner.id] = company

        db.flush()
        sample_jobs = [
            ("Junior Java Developer", "Java, SQL, Testing", "Full-time", "On-site", "Fresher", "Bengaluru", False, None, None),
            ("Python Backend Intern", "Python, SQL, Cloud", "Internship", "Hybrid", "Fresher", "Pune", False, None, None),
            ("Salesforce Trainee", "Salesforce, Testing, SQL", "Full-time", "Remote", "0-1 years", "Remote", True, 1.0, "One-year service agreement after training completion."),
            ("Data Science Intern", "Data Science, Python, Machine Learning", "Internship", "Hybrid", "Fresher", "Hyderabad", False, None, None),
            ("Web Development Associate", "Web Development, React, Node.js", "Full-time", "On-site", "0-1 years", "Mumbai", True, 2.0, "Two-year bond for candidates who join the sponsored training track."),
            ("React Frontend Intern", "React, UI/UX, Testing", "Internship", "Remote", "Fresher", "Remote", False, None, None),
            ("Cloud Support Engineer", "Cloud, SQL, Testing", "Full-time", "Hybrid", "0-1 years", "Chennai", True, 1.0, "One-year service agreement for cloud certification sponsorship."),
            ("QA Testing Intern", "Testing, Java, SQL", "Internship", "On-site", "Fresher", "Bengaluru", False, None, None),
            ("Machine Learning Trainee", "Machine Learning, Python, Data Science", "Full-time", "Hybrid", "0-1 years", "Delhi", True, 2.0, "Two-year agreement applies after paid AI training."),
            ("Node.js API Developer", "Node.js, SQL, Cloud", "Full-time", "Remote", "1-2 years", "Remote", False, None, None),
            ("UI/UX Design Intern", "UI/UX, Web Development, Testing", "Internship", "Hybrid", "Fresher", "Ahmedabad", False, None, None),
            ("SQL Data Analyst", "SQL, Data Science, Python", "Full-time", "On-site", "0-1 years", "Gurugram", True, 1.0, "One-year bond for candidates receiving analytics bootcamp sponsorship."),
            ("Full Stack Fresher", "React, Node.js, Python, SQL", "Full-time", "Hybrid", "Fresher", "Bengaluru", False, None, None),
            ("Salesforce QA Associate", "Salesforce, Testing, Cloud", "Contract", "Remote", "1-2 years", "Remote", False, None, None),
            ("AI Product Intern", "Machine Learning, Python, UI/UX", "Internship", "Hybrid", "Fresher", "Pune", False, None, None),
        ]
        if db.scalar(select(Job).limit(1)) is None:
            for index, (title, required_skills, job_type, work_mode, exp, location, has_bond, bond_years, bond_details) in enumerate(sample_jobs):
                owner = recruiter if index % 2 == 0 else recruiter_two
                company = company_by_recruiter_id[owner.id]
                company_name = "NovaWorks Labs" if owner.id == recruiter.id else "CloudNest Systems"
                db.add(
                    Job(
                        recruiter_id=owner.id,
                        company_id=company.id,
                        title=title,
                        company_name=company_name,
                        location=location,
                        job_type=job_type,
                        work_mode=work_mode,
                        salary="INR 4 LPA - INR 8 LPA" if job_type != "Internship" else "INR 15,000 - INR 30,000 / month",
                        required_skills=required_skills,
                        required_experience_level=exp,
                        description=(
                            "Work with a supportive team on real product problems, ship clean code, "
                            "and build a portfolio-ready project experience."
                        ),
                        eligibility="Freshers and early-career candidates with strong fundamentals may apply.",
                        deadline=date.today() + timedelta(days=20 + index),
                        is_active=True,
                        has_bond=has_bond,
                        bond_years=bond_years,
                        bond_details=bond_details,
                    )
                )
        else:
            for title, _required_skills, _job_type, _work_mode, _exp, _location, has_bond, bond_years, bond_details in sample_jobs:
                job = db.scalar(select(Job).where(Job.title == title))
                if job:
                    if job.recruiter_id in company_by_recruiter_id:
                        job.company_id = company_by_recruiter_id[job.recruiter_id].id
                    job.has_bond = has_bond
                    job.bond_years = bond_years
                    job.bond_details = bond_details
        db.commit()

        first_jobs = db.scalars(select(Job).order_by(Job.id).limit(5)).all()
        if first_jobs and db.scalar(select(Application).limit(1)) is None:
            db.add(Application(job_seeker_id=seeker.id, job_id=first_jobs[0].id, status=ApplicationStatus.APPLIED.value))
            db.add(Application(job_seeker_id=seeker.id, job_id=first_jobs[1].id, status=ApplicationStatus.VIEWED.value))
            db.add(Application(job_seeker_id=seeker_two.id, job_id=first_jobs[2].id, status=ApplicationStatus.SHORTLISTED.value))
        if first_jobs and db.scalar(select(Swipe).limit(1)) is None:
            db.add(Swipe(job_seeker_id=seeker.id, job_id=first_jobs[0].id, action=SwipeAction.LIKE.value))
            db.add(Swipe(job_seeker_id=seeker.id, job_id=first_jobs[3].id, action=SwipeAction.SAVE.value))
            db.add(Swipe(job_seeker_id=seeker.id, job_id=first_jobs[4].id, action=SwipeAction.REJECT.value))
            db.add(Swipe(job_seeker_id=seeker_two.id, job_id=first_jobs[1].id, action=SwipeAction.SAVE.value))

        db.flush()
        shortlisted_application = db.scalar(
            select(Application)
            .join(Job)
            .where(Application.status == ApplicationStatus.SHORTLISTED.value)
            .order_by(Application.id)
        )
        if shortlisted_application and db.scalar(select(ChatThread).where(ChatThread.application_id == shortlisted_application.id)) is None:
            chat_thread = ChatThread(
                application_id=shortlisted_application.id,
                recruiter_id=shortlisted_application.job.recruiter_id,
                job_seeker_id=shortlisted_application.job_seeker_id,
                job_id=shortlisted_application.job_id,
                status=ChatThreadStatus.ACTIVE.value,
                started_by_recruiter=True,
            )
            db.add(chat_thread)
            db.flush()
            db.add(
                ChatMessage(
                    thread_id=chat_thread.id,
                    sender_id=shortlisted_application.job.recruiter_id,
                    message_text="Hi, your profile has been shortlisted. Are you available for a quick discussion this week?",
                )
            )
            db.add(
                ChatMessage(
                    thread_id=chat_thread.id,
                    sender_id=shortlisted_application.job_seeker_id,
                    message_text="Thank you for shortlisting me. I am available and happy to discuss the role.",
                    is_read=True,
                )
            )

        db.flush()
        for application in db.scalars(select(Application)).all():
            if db.scalar(select(ApplicationTimeline).where(ApplicationTimeline.application_id == application.id).limit(1)) is None:
                db.add(
                    ApplicationTimeline(
                        application_id=application.id,
                        action=application.status,
                        old_status=None,
                        new_status=application.status,
                        note=f"Seed timeline event for {application.status.lower()} application.",
                        created_by_user_id=application.job_seeker_id,
                    )
                )
                if application.chat_thread:
                    db.add(
                        ApplicationTimeline(
                            application_id=application.id,
                            action="CHAT_STARTED",
                            old_status=application.status,
                            new_status=application.status,
                            note="Seed recruiter-started chat.",
                            created_by_user_id=application.chat_thread.recruiter_id,
                        )
                    )

        if db.scalar(select(Notification).limit(1)) is None:
            db.add(
                Notification(
                    user_id=seeker.id,
                    title="Welcome to Swipe for Success",
                    message="Complete your profile to improve job match scores.",
                    type="ADMIN_ACTION",
                    link_url="/jobseeker/profile",
                )
            )
            db.add(
                Notification(
                    user_id=recruiter.id,
                    title="Recruiter verified",
                    message="Your seed recruiter account is verified and can post jobs.",
                    type="RECRUITER_VERIFIED",
                    link_url="/recruiter/dashboard",
                )
            )

        if db.scalar(select(Report).limit(1)) is None and first_jobs:
            db.add(
                Report(
                    reporter_id=seeker.id,
                    job_id=first_jobs[0].id,
                    recruiter_id=first_jobs[0].recruiter_id,
                    report_type=ReportType.MISLEADING_INFO.value,
                    description="Seed report for admin moderation demonstration.",
                    status=ReportStatus.PENDING.value,
                )
            )

        db.commit()
        for message in team_account_messages:
            print(message)
        _ = admin
        _ = owner
        print("Seed data created or already present.")
        print("Demo credentials are documented for local development only.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
