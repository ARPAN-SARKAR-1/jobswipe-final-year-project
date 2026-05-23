from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.company_review import CompanyReview


def recalculate_company_rating(db: Session, company_id: int) -> None:
    average_rating, total_reviews = db.execute(
        select(func.avg(CompanyReview.rating), func.count(CompanyReview.id))
        .where(CompanyReview.company_id == company_id)
        .where(CompanyReview.is_visible.is_(True))
    ).one()
    company = db.get(Company, company_id)
    if company is None:
        return
    company.average_rating = round(float(average_rating or 0), 2)
    company.total_reviews = int(total_reviews or 0)
