from enum import Enum


class UserRole(str, Enum):
    OWNER = "OWNER"
    JOB_SEEKER = "JOB_SEEKER"
    RECRUITER = "RECRUITER"
    ADMIN = "ADMIN"


class AccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


class JobModerationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    REMOVED = "REMOVED"


class ApplicationAdminStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"


class RecruiterVerificationStatus(str, Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"


class JobSeekerVerificationStatus(str, Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"


class JobSeekerCategory(str, Enum):
    UNDERGRADUATE = "UNDERGRADUATE"
    GRADUATE_FRESHER = "GRADUATE_FRESHER"
    GRADUATE_EXPERIENCED = "GRADUATE_EXPERIENCED"


class StudentVerificationStatus(str, Enum):
    STUDENT_UNVERIFIED = "STUDENT_UNVERIFIED"
    STUDENT_PENDING = "STUDENT_PENDING"
    STUDENT_VERIFIED = "STUDENT_VERIFIED"
    STUDENT_REJECTED = "STUDENT_REJECTED"


class GraduationVerificationStatus(str, Enum):
    GRADUATION_UNVERIFIED = "GRADUATION_UNVERIFIED"
    GRADUATION_PENDING = "GRADUATION_PENDING"
    GRADUATION_VERIFIED = "GRADUATION_VERIFIED"
    GRADUATION_REJECTED = "GRADUATION_REJECTED"


class ExperienceVerificationStatus(str, Enum):
    EXPERIENCE_UNVERIFIED = "EXPERIENCE_UNVERIFIED"
    EXPERIENCE_PENDING = "EXPERIENCE_PENDING"
    EXPERIENCE_VERIFIED = "EXPERIENCE_VERIFIED"
    EXPERIENCE_REJECTED = "EXPERIENCE_REJECTED"


class SectionVisibility(str, Enum):
    PRIVATE = "PRIVATE"
    RECRUITERS_ONLY = "RECRUITERS_ONLY"
    PUBLIC = "PUBLIC"


class DocumentVerificationStatus(str, Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class ProfileVisibility(str, Enum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"


class CompanyType(str, Enum):
    STARTUP = "STARTUP"
    MNC = "MNC"
    CONSULTANCY = "CONSULTANCY"
    AGENCY = "AGENCY"
    COLLEGE = "COLLEGE"
    OTHER = "OTHER"


class CompanyVerificationStatus(str, Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"


class CompanyJoinStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ReviewModerationStatus(str, Enum):
    VISIBLE = "VISIBLE"
    HIDDEN = "HIDDEN"
    FLAGGED = "FLAGGED"
    REMOVED = "REMOVED"


class ChatThreadStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    PAUSED = "PAUSED"


class SwipeAction(str, Enum):
    LIKE = "LIKE"
    REJECT = "REJECT"
    SAVE = "SAVE"


class ApplicationStatus(str, Enum):
    APPLIED = "APPLIED"
    VIEWED = "VIEWED"
    SHORTLISTED = "SHORTLISTED"
    INTERVIEWED = "INTERVIEWED"
    HIRED = "HIRED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"


class ReportType(str, Enum):
    FAKE_JOB = "FAKE_JOB"
    ASKING_MONEY = "ASKING_MONEY"
    MISLEADING_INFO = "MISLEADING_INFO"
    ABUSIVE = "ABUSIVE"
    SPAM = "SPAM"
    OTHER = "OTHER"


class ReportStatus(str, Enum):
    PENDING = "PENDING"
    REVIEWED = "REVIEWED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class JobType(str, Enum):
    INTERNSHIP = "Internship"
    FULL_TIME = "Full-time"
    PART_TIME = "Part-time"
    REMOTE = "Remote"
    HYBRID = "Hybrid"
    CONTRACT = "Contract"


class WorkMode(str, Enum):
    ON_SITE = "On-site"
    REMOTE = "Remote"
    HYBRID = "Hybrid"


class ExperienceLevel(str, Enum):
    FRESHER = "Fresher"
    ZERO_ONE = "0-1 years"
    ONE_TWO = "1-2 years"
    TWO_PLUS = "2+ years"
