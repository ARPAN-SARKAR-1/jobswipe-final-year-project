from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import re
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.application import Application
from app.models.enums import ApplicationStatus, SwipeAction
from app.models.job import Job
from app.models.job_seeker_profile import JobSeekerProfile
from app.models.swipe import Swipe
from app.utils.skills import split_skills


ACTION_WEIGHTS = {
    SwipeAction.LIKE.value: 3.0,
    SwipeAction.SAVE.value: 4.0,
    SwipeAction.REJECT.value: -3.0,
}

APPLICATION_WEIGHTS = {
    ApplicationStatus.APPLIED.value: 5.0,
    ApplicationStatus.VIEWED.value: 1.0,
    ApplicationStatus.SHORTLISTED.value: 5.5,
    ApplicationStatus.INTERVIEWED.value: 6.0,
    ApplicationStatus.HIRED.value: 7.0,
    ApplicationStatus.REJECTED.value: 2.0,
    ApplicationStatus.WITHDRAWN.value: 1.0,
}

TITLE_STOPWORDS = {
    "and",
    "for",
    "the",
    "with",
    "job",
    "role",
    "open",
    "hiring",
    "urgent",
    "required",
    "full",
    "time",
    "part",
}

BUCKET_REASON_LABELS = {
    "skills": "roles",
    "locations": "jobs",
    "work_modes": "roles",
    "job_types": "roles",
    "companies": "opportunities",
    "industries": "companies",
    "experience_levels": "roles",
    "title_keywords": "roles",
}


@dataclass
class RecommendationPreferences:
    scores: dict[str, dict[str, float]] = field(default_factory=lambda: defaultdict(lambda: defaultdict(float)))
    labels: dict[str, dict[str, str]] = field(default_factory=lambda: defaultdict(dict))
    total_interactions: int = 0
    profile_fallback_used: bool = False


@dataclass
class RecommendationScore:
    job: Job
    score: float
    exploration_score: float
    reason: str | None


def normalize_key(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def title_keywords(value: str | None) -> list[str]:
    if not value:
        return []
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.\-]{2,}", value.lower())
    return [word for word in words if word not in TITLE_STOPWORDS]


def add_preference(preferences: RecommendationPreferences, bucket: str, value: str | None, amount: float, label: str | None = None) -> None:
    key = normalize_key(value)
    if not key:
        return
    preferences.scores[bucket][key] += amount
    preferences.labels[bucket].setdefault(key, label or value or key)


def recency_factor(created_at: datetime | None, index: int) -> float:
    factor = 1.0 if index < 20 else 0.65 if index < 50 else 0.4
    if not created_at:
        return factor
    now = datetime.utcnow()
    if created_at >= now - timedelta(days=7):
        return factor * 1.15
    if created_at < now - timedelta(days=30):
        return factor * 0.75
    return factor


def add_job_attributes(preferences: RecommendationPreferences, job: Job, amount: float) -> None:
    if amount == 0:
        return
    for skill in split_skills(job.required_skills):
        add_preference(preferences, "skills", skill, amount, skill)
    add_preference(preferences, "locations", job.location, amount * 0.9, job.location)
    add_preference(preferences, "work_modes", job.work_mode, amount * 0.85, job.work_mode)
    add_preference(preferences, "job_types", job.job_type, amount * 0.85, job.job_type)
    add_preference(preferences, "experience_levels", job.required_experience_level, amount * 0.65, job.required_experience_level)
    add_preference(preferences, "companies", job.company_name, amount * 0.4, job.company_name)
    if job.company and job.company.industry:
        add_preference(preferences, "industries", job.company.industry, amount * 0.45, job.company.industry)
    for keyword in title_keywords(job.title):
        add_preference(preferences, "title_keywords", keyword, amount * 0.65, keyword)


def add_profile_fallback(preferences: RecommendationPreferences, profile: JobSeekerProfile | None, scale: float = 1.0) -> None:
    if profile is None:
        return
    preferences.profile_fallback_used = True
    for skill_source in [profile.skills, profile.fresher_skills, profile.tools_technologies, profile.certifications]:
        for skill in split_skills(skill_source):
            add_preference(preferences, "skills", skill, 2.0 * scale, skill)
    add_preference(preferences, "locations", profile.preferred_location or profile.college_location, 1.8 * scale, profile.preferred_location or profile.college_location)
    add_preference(preferences, "job_types", profile.preferred_job_type, 1.4 * scale, profile.preferred_job_type)
    add_preference(preferences, "experience_levels", profile.experience_level, 1.2 * scale, profile.experience_level)

    if profile.job_seeker_category == "UNDERGRADUATE":
        add_preference(preferences, "job_types", "Internship", 1.7 * scale, "Internship")
        add_preference(preferences, "title_keywords", "internship", 1.4 * scale, "Internship")
        for role in split_skills(profile.preferred_internship_roles):
            add_preference(preferences, "title_keywords", role, 1.2 * scale, role)
    elif profile.job_seeker_category == "GRADUATE_FRESHER":
        add_preference(preferences, "experience_levels", "Fresher", 1.7 * scale, "Fresher")
        for role in split_skills(profile.preferred_job_roles):
            add_preference(preferences, "title_keywords", role, 1.2 * scale, role)
    elif profile.job_seeker_category == "GRADUATE_EXPERIENCED":
        add_preference(preferences, "title_keywords", profile.current_or_last_role, 1.4 * scale, profile.current_or_last_role)
        for role in split_skills(profile.preferred_next_roles):
            add_preference(preferences, "title_keywords", role, 1.2 * scale, role)


def build_user_swipe_preferences(db: Session, user_id: int, history_limit: int = 100) -> RecommendationPreferences:
    preferences = RecommendationPreferences()
    swipes = list(
        db.scalars(
            select(Swipe)
            .options(joinedload(Swipe.job).joinedload(Job.company))
            .where(Swipe.job_seeker_id == user_id)
            .order_by(Swipe.created_at.desc(), Swipe.id.desc())
            .limit(history_limit)
        ).all()
    )
    for index, swipe in enumerate(swipes):
        if not swipe.job:
            continue
        base_weight = ACTION_WEIGHTS.get(swipe.action, 0.0)
        add_job_attributes(preferences, swipe.job, base_weight * recency_factor(swipe.created_at, index))
        preferences.total_interactions += 1

    applications = list(
        db.scalars(
            select(Application)
            .options(joinedload(Application.job).joinedload(Job.company))
            .where(Application.job_seeker_id == user_id)
            .order_by(Application.created_at.desc(), Application.id.desc())
            .limit(50)
        ).all()
    )
    for index, application in enumerate(applications):
        if not application.job:
            continue
        base_weight = APPLICATION_WEIGHTS.get(application.status, 5.0)
        add_job_attributes(preferences, application.job, base_weight * recency_factor(application.created_at, index))
        preferences.total_interactions += 1

    profile = db.scalar(select(JobSeekerProfile).where(JobSeekerProfile.user_id == user_id))
    add_profile_fallback(preferences, profile, scale=1.0 if preferences.total_interactions == 0 else 0.35)
    return preferences


def bucket_score(job_value: str | None, values: dict[str, float]) -> tuple[float, str | None]:
    normalized = normalize_key(job_value)
    if not normalized:
        return 0.0, None
    score = 0.0
    matched_key: str | None = None
    for key, value in values.items():
        if key == normalized or key in normalized or normalized in key:
            score += value
            if value > 0 and (matched_key is None or value > values.get(matched_key, 0)):
                matched_key = key
    return score, matched_key


def score_job_for_user(job: Job, preferences: RecommendationPreferences) -> RecommendationScore:
    total_score = 0.0
    reason_candidates: list[tuple[float, str, str]] = []

    def add_bucket(bucket: str, value: str | None, multiplier: float = 1.0) -> None:
        nonlocal total_score
        score, key = bucket_score(value, preferences.scores.get(bucket, {}))
        weighted_score = score * multiplier
        total_score += weighted_score
        if key and weighted_score > 0:
            label = preferences.labels.get(bucket, {}).get(key, key)
            reason_candidates.append((weighted_score, bucket, label))

    for skill in split_skills(job.required_skills):
        add_bucket("skills", skill, 1.0)
    add_bucket("locations", job.location, 0.9)
    add_bucket("work_modes", job.work_mode, 0.85)
    add_bucket("job_types", job.job_type, 0.85)
    add_bucket("experience_levels", job.required_experience_level, 0.65)
    add_bucket("companies", job.company_name, 0.4)
    if job.company and job.company.industry:
        add_bucket("industries", job.company.industry, 0.45)
    for keyword in title_keywords(job.title):
        add_bucket("title_keywords", keyword, 0.65)

    match_score = getattr(job, "match_score", None)
    if isinstance(match_score, int | float):
        total_score += min(3.0, max(0.0, float(match_score) / 40.0))

    trusted_bonus = 0.0
    if getattr(job, "trusted_posting", False):
        trusted_bonus += 1.0
    elif getattr(job, "company_verified", False):
        trusted_bonus += 0.6
    if job.career_page_url:
        trusted_bonus += 0.35
    total_score += trusted_bonus

    fresh_bonus = freshness_score(job)
    total_score += fresh_bonus

    reason = recommendation_reason(reason_candidates, preferences, job)
    return RecommendationScore(job=job, score=total_score, exploration_score=fresh_bonus + trusted_bonus, reason=reason)


def freshness_score(job: Job) -> float:
    if not job.created_at:
        return 0.0
    age_days = max(0, (datetime.utcnow() - job.created_at).days)
    if age_days <= 7:
        return 0.8
    if age_days <= 30:
        return 0.35
    return 0.0


def recommendation_reason(reason_candidates: list[tuple[float, str, str]], preferences: RecommendationPreferences, job: Job) -> str | None:
    if reason_candidates:
        _, bucket, label = max(reason_candidates, key=lambda item: item[0])
        if bucket == "locations":
            return f"Recommended because you often choose {label} jobs"
        if bucket == "work_modes":
            return f"Recommended because you prefer {label} roles"
        if bucket == "job_types":
            return f"Recommended because you interact with {label} roles"
        if bucket == "companies":
            return f"Recommended based on companies you saved or applied to"
        if bucket == "industries":
            return f"Recommended because you like {label} companies"
        return f"Recommended because you like {label} {BUCKET_REASON_LABELS.get(bucket, 'roles')}"
    if preferences.profile_fallback_used and split_skills(job.required_skills):
        return "Recommended based on your profile skills"
    if getattr(job, "trusted_posting", False):
        return "Verified company match"
    return None


def blend_ranked_and_diverse(scored_jobs: Iterable[RecommendationScore], limit: int) -> list[RecommendationScore]:
    scored = list(scored_jobs)
    ranked = sorted(scored, key=lambda item: (item.score, item.exploration_score, item.job.created_at or datetime.min), reverse=True)
    diverse = sorted(scored, key=lambda item: (item.exploration_score, item.job.created_at or datetime.min), reverse=True)
    selected: list[RecommendationScore] = []
    seen: set[int] = set()
    ranked_index = 0
    diverse_index = 0

    def take_from(source: list[RecommendationScore], start_index: int) -> int:
        nonlocal selected
        index = start_index
        while index < len(source):
            item = source[index]
            index += 1
            if item.job.id not in seen:
                selected.append(item)
                seen.add(item.job.id)
                break
        return index

    while len(selected) < min(limit, len(scored)) and (ranked_index < len(ranked) or diverse_index < len(diverse)):
        for _ in range(4):
            if len(selected) >= limit:
                break
            ranked_index = take_from(ranked, ranked_index)
        if len(selected) >= limit:
            break
        diverse_index = take_from(diverse, diverse_index)
    return selected[:limit]


def get_behavior_ranked_jobs(db: Session, user_id: int, candidate_jobs: list[Job], limit: int = 50) -> list[Job]:
    preferences = build_user_swipe_preferences(db, user_id)
    scored = [score_job_for_user(job, preferences) for job in candidate_jobs]
    ranked = blend_ranked_and_diverse(scored, limit)
    for item in ranked:
        setattr(item.job, "recommendation_score", round(item.score, 2))
        setattr(item.job, "recommendation_reason", item.reason)
    return [item.job for item in ranked]
