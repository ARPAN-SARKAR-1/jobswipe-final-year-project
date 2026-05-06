from app.models.job import Job
from app.models.job_seeker_profile import JobSeekerProfile
from app.utils.skills import split_skills


def calculate_match_score(job: Job, profile: JobSeekerProfile | None) -> dict:
    job_skills = split_skills(job.required_skills)
    profile_skills = split_skills(profile.skills if profile else None)
    if not profile or not profile_skills:
        return {
            "match_score": None,
            "matched_skills": [],
            "missing_skills": job_skills,
            "match_note": "Complete your profile to improve match score.",
        }

    job_skill_keys = {skill.lower(): skill for skill in job_skills}
    profile_skill_keys = {skill.lower(): skill for skill in profile_skills}
    matched_keys = set(job_skill_keys).intersection(profile_skill_keys)
    matched_skills = [job_skill_keys[key] for key in matched_keys]
    missing_skills = [skill for key, skill in job_skill_keys.items() if key not in matched_keys]

    skill_score = (len(matched_keys) / len(job_skill_keys) * 50) if job_skill_keys else 0
    experience_score = 20 if profile.experience_level and profile.experience_level == job.required_experience_level else 0
    job_type_score = 15 if profile.preferred_job_type and profile.preferred_job_type == job.job_type else 0

    location_score = 0
    preferred_location = (profile.preferred_location or "").strip().lower()
    if preferred_location:
        if preferred_location in job.location.lower() or preferred_location in job.work_mode.lower():
            location_score = 15
        elif job.work_mode.lower() in {"remote", "hybrid"} and preferred_location == "remote":
            location_score = 15

    return {
        "match_score": min(100, round(skill_score + experience_score + job_type_score + location_score)),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "match_note": None,
    }
