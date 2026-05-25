from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.recruiter_profile import RecruiterProfile
from app.models.recruiter_review import RecruiterReview
from app.services.review_moderation import keyword_summary


def recalculate_recruiter_rating(db: Session, recruiter_id: int) -> None:
    average_rating, total_reviews = db.execute(
        select(func.avg(RecruiterReview.overall_rating), func.count(RecruiterReview.id))
        .where(RecruiterReview.recruiter_id == recruiter_id)
        .where(RecruiterReview.is_visible.is_(True))
    ).one()
    profile = db.scalar(select(RecruiterProfile).where(RecruiterProfile.user_id == recruiter_id))
    if profile is None:
        return
    profile.average_rating = round(float(average_rating or 0), 2)
    profile.total_reviews = int(total_reviews or 0)


def recruiter_review_summary(db: Session, recruiter_id: int) -> dict:
    row = db.execute(
        select(
            func.avg(RecruiterReview.overall_rating),
            func.avg(RecruiterReview.communication_rating),
            func.avg(RecruiterReview.response_time_rating),
            func.avg(RecruiterReview.professionalism_rating),
            func.avg(RecruiterReview.transparency_rating),
            func.count(RecruiterReview.id),
            func.sum(case((RecruiterReview.moderation_status == "FLAGGED", 1), else_=0)),
            func.sum(case((RecruiterReview.moderation_status == "HIDDEN", 1), else_=0)),
        )
        .where(RecruiterReview.recruiter_id == recruiter_id)
        .where(RecruiterReview.is_visible.is_(True))
    ).one()
    reviews = db.scalars(
        select(RecruiterReview)
        .where(RecruiterReview.recruiter_id == recruiter_id)
        .where(RecruiterReview.is_visible.is_(True))
    ).all()
    return {
        "recruiter_id": recruiter_id,
        "average_overall_rating": round(float(row[0] or 0), 2),
        "communication_average": round(float(row[1] or 0), 2),
        "response_time_average": round(float(row[2] or 0), 2),
        "professionalism_average": round(float(row[3] or 0), 2),
        "transparency_average": round(float(row[4] or 0), 2),
        "total_reviews": int(row[5] or 0),
        "flagged_reviews": int(row[6] or 0),
        "hidden_reviews": int(row[7] or 0),
        "top_feedback_keywords": keyword_summary([review.review_text for review in reviews]),
    }
