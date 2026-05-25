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

    skill_score = (len(matched_keys) / len(job_skill_keys) * 45) if job_skill_keys else 0
    experience_score = 15 if profile.experience_level and profile.experience_level == job.required_experience_level else 0
    job_type_score = 10 if profile.preferred_job_type and profile.preferred_job_type == job.job_type else 0

    academic_score = 0
    if job.eligible_academic_status == "BOTH" or not profile.academic_status:
        academic_score += 5
    elif job.eligible_academic_status == profile.academic_status:
        academic_score += 10
    else:
        academic_score -= 20

    if job.internship_available and profile.academic_status == "UNDERGRADUATE":
        academic_score += 5
    if job.job_type == "Full-time" and profile.academic_status == "GRADUATE":
        academic_score += 5
    if job.eligible_streams and profile.stream_or_branch:
        stream_filters = {item.lower() for item in split_skills(job.eligible_streams)}
        if profile.stream_or_branch.lower() in stream_filters:
            academic_score += 5
    if job.minimum_cgpa is not None and profile.current_cgpa is not None:
        academic_score += 5 if profile.current_cgpa >= job.minimum_cgpa else -10
    if job.eligible_graduation_years:
        years = {item.strip() for item in job.eligible_graduation_years.split(",") if item.strip()}
        candidate_year = profile.expected_graduation_year or profile.passing_year
        if candidate_year and str(candidate_year) in years:
            academic_score += 5

    location_score = 0
    preferred_location = (profile.preferred_location or "").strip().lower()
    if preferred_location:
        if preferred_location in job.location.lower() or preferred_location in job.work_mode.lower():
            location_score = 15
        elif job.work_mode.lower() in {"remote", "hybrid"} and preferred_location == "remote":
            location_score = 15

    return {
        "match_score": max(0, min(100, round(skill_score + experience_score + job_type_score + location_score + academic_score))),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "match_note": None,
    }
