from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.company_review import CompanyReview
from app.services.review_moderation import keyword_summary


def recalculate_company_rating(db: Session, company_id: int) -> None:
    average_rating, total_reviews = db.execute(
        select(func.avg(CompanyReview.overall_rating), func.count(CompanyReview.id))
        .where(CompanyReview.company_id == company_id)
        .where(CompanyReview.is_visible.is_(True))
    ).one()
    company = db.get(Company, company_id)
    if company is None:
        return
    company.average_rating = round(float(average_rating or 0), 2)
    company.total_reviews = int(total_reviews or 0)


def company_review_summary(db: Session, company_id: int) -> dict:
    row = db.execute(
        select(
            func.avg(CompanyReview.overall_rating),
            func.avg(CompanyReview.work_culture_rating),
            func.avg(CompanyReview.interview_process_rating),
            func.avg(CompanyReview.salary_transparency_rating),
            func.avg(CompanyReview.growth_opportunity_rating),
            func.count(CompanyReview.id),
            func.sum(case((CompanyReview.moderation_status == "FLAGGED", 1), else_=0)),
            func.sum(case((CompanyReview.moderation_status == "HIDDEN", 1), else_=0)),
        )
        .where(CompanyReview.company_id == company_id)
        .where(CompanyReview.is_visible.is_(True))
    ).one()
    reviews = db.scalars(
        select(CompanyReview)
        .where(CompanyReview.company_id == company_id)
        .where(CompanyReview.is_visible.is_(True))
    ).all()
    return {
        "company_id": company_id,
        "average_overall_rating": round(float(row[0] or 0), 2),
        "work_culture_average": round(float(row[1] or 0), 2),
        "interview_process_average": round(float(row[2] or 0), 2),
        "salary_transparency_average": round(float(row[3] or 0), 2),
        "growth_opportunity_average": round(float(row[4] or 0), 2),
        "total_reviews": int(row[5] or 0),
        "flagged_reviews": int(row[6] or 0),
        "hidden_reviews": int(row[7] or 0),
        "top_positive_keywords": keyword_summary([review.pros or review.review_text for review in reviews]),
        "top_negative_keywords": keyword_summary([review.cons for review in reviews]),
    }
