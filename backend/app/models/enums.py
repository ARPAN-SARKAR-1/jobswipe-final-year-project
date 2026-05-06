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
