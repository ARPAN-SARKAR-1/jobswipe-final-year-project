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


class CompanyMemberRole(str, Enum):
    COMPANY_OWNER = "COMPANY_OWNER"
    COMPANY_ADMIN = "COMPANY_ADMIN"
    COMPANY_RECRUITER = "COMPANY_RECRUITER"


class CompanyClaimStatus(str, Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class CompanyVerificationStatus(str, Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class CompanyType(str, Enum):
    MNC = "MNC"
    STARTUP = "Startup"
    PRODUCT_BASED = "Product-based"
    SERVICE_BASED = "Service-based"
    CONSULTANCY = "Consultancy"
    GOVERNMENT = "Government"
    NON_PROFIT = "Non-profit"
    OTHER = "Other"


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


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskAutoAction(str, Enum):
    NONE = "NONE"
    FLAGGED = "FLAGGED"
    PAUSED = "PAUSED"


class ReviewModerationStatus(str, Enum):
    VISIBLE = "VISIBLE"
    HIDDEN = "HIDDEN"
    FLAGGED = "FLAGGED"


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
