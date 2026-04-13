from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import Company, Experience
from app.schemas import CompanyOut, CompanyDetail, ExperienceOut

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("", response_model=List[CompanyOut])
def list_companies(
    db: Session = Depends(get_db),
    sector: Optional[str] = None,
    difficulty: Optional[str] = None,
    max_cgpa: Optional[float] = Query(None, description="Filter by eligibility <= max_cgpa"),
):
    q = db.query(Company)
    if sector:
        q = q.filter(Company.sector == sector)
    if difficulty:
        q = q.filter(Company.difficulty == difficulty)
    if max_cgpa is not None:
        q = q.filter(Company.eligibility_cgpa <= max_cgpa)
    return q.order_by(Company.name).all()


@router.get("/{company_id}", response_model=CompanyDetail)
def get_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    experiences = (
        db.query(Experience)
        .filter(Experience.company_id == company_id)
        .order_by(Experience.created_at.desc())
        .limit(10)
        .all()
    )
    detail = CompanyDetail.model_validate(company)
    detail.experiences = [ExperienceOut.model_validate(e) for e in experiences]
    return detail
