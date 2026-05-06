from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.application import Application
from app.models.application_timeline import ApplicationTimeline
from app.models.chat_message import ChatMessage
from app.models.chat_thread import ChatThread
from app.models.company_profile import CompanyProfile
from app.models.enums import ApplicationStatus, ChatThreadStatus, RecruiterVerificationStatus, ReportStatus, ReportType, SwipeAction, UserRole
from app.models.job import Job
from app.models.job_seeker_profile import JobSeekerProfile
from app.models.notification import Notification
from app.models.report import Report
from app.models.swipe import Swipe
from app.models.user import User


def get_or_create_user(db, name: str, email: str, password: str, role: UserRole) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user:
        user.role = role.value
        if user.account_status is None:
            user.account_status = "ACTIVE"
        return user
    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role=role.value,
        accepted_terms=True,
        accepted_terms_at=datetime.now(timezone.utc).replace(tzinfo=None),
        accepted_privacy=True,
        accepted_privacy_at=datetime.now(timezone.utc).replace(tzinfo=None),
        account_status="ACTIVE",
    )
    db.add(user)
    db.flush()
    return user


def main() -> None:
    db = SessionLocal()
    try:
        owner = get_or_create_user(db, "Owner User", "owner@jobswipe.dev", "Owner@123", UserRole.OWNER)
        owner.is_protected_owner = True
        owner.account_status = "ACTIVE"
        owner.suspension_reason = None
        owner.accepted_privacy = True
        owner.accepted_privacy_at = owner.accepted_privacy_at or datetime.now(timezone.utc).replace(tzinfo=None)
        admin = get_or_create_user(db, "Admin User", "admin@jobswipe.dev", "Admin@123", UserRole.ADMIN)
        admin.is_protected_owner = False
        admin.account_status = "ACTIVE"
        admin.suspension_reason = None
        admin.accepted_privacy = True
        admin.accepted_privacy_at = admin.accepted_privacy_at or datetime.now(timezone.utc).replace(tzinfo=None)
        seeker = get_or_create_user(db, "Aarav Sharma", "jobseeker@jobswipe.dev", "Jobseeker@123", UserRole.JOB_SEEKER)
        seeker_two = get_or_create_user(db, "Meera Iyer", "meera@jobswipe.dev", "Jobseeker@123", UserRole.JOB_SEEKER)
        recruiter = get_or_create_user(db, "Neha Recruiter", "recruiter@jobswipe.dev", "Recruiter@123", UserRole.RECRUITER)
        recruiter_two = get_or_create_user(db, "Rohan Hiring", "rohan@jobswipe.dev", "Recruiter@123", UserRole.RECRUITER)
        for seeded_user in [seeker, seeker_two, recruiter, recruiter_two]:
            seeded_user.accepted_privacy = True
            seeded_user.accepted_privacy_at = seeded_user.accepted_privacy_at or datetime.now(timezone.utc).replace(tzinfo=None)
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
            (recruiter, "NovaWorks Labs", "https://novaworks.example", "Bengaluru", "Product engineering studio hiring fresh talent."),
            (recruiter_two, "CloudNest Systems", "https://cloudnest.example", "Hyderabad", "Cloud and data consultancy for fast-growing teams."),
        ]
        for company_owner, name, website, location, description in companies:
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
                company.verified_at or datetime.now(timezone.utc).replace(tzinfo=None)
                if company_owner.id == recruiter.id
                else None
            )
            company.verified_by_admin_id = admin.id if company_owner.id == recruiter.id else None

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
                company_name = "NovaWorks Labs" if owner.id == recruiter.id else "CloudNest Systems"
                db.add(
                    Job(
                        recruiter_id=owner.id,
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
                    title="Welcome to JobSwipe",
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
        _ = admin
        _ = owner
        print("Seed data created or already present.")
        print("Demo credentials:")
        print("owner@jobswipe.dev / Owner@123")
        print("admin@jobswipe.dev / Admin@123")
        print("jobseeker@jobswipe.dev / Jobseeker@123")
        print("recruiter@jobswipe.dev / Recruiter@123")
    finally:
        db.close()


if __name__ == "__main__":
    main()
