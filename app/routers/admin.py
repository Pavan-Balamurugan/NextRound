from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.deps import get_db, require_placement_officer, require_alumni_or_officer
from app.models import User, Company, Experience
from app.schemas import (
    StudentSummary, PlacementUpdate, AdminStats,
    CompanyCreate, CompanyUpdate, CompanyOut
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStats)
def get_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_placement_officer),
):
    total_students = db.query(User).filter(User.role == "student").count()
    placed = db.query(User).filter(User.role == "student", User.placement_status == "placed").count()
    return AdminStats(
        total_students=total_students,
        placed_students=placed,
        unplaced_students=total_students - placed,
        total_companies=db.query(Company).count(),
        total_experiences=db.query(Experience).count(),
        placement_percentage=round((placed / total_students * 100) if total_students else 0, 1),
    )


@router.get("/students", response_model=List[StudentSummary])
def list_students(
    status_filter: str = "all",  # all | placed | unplaced
    db: Session = Depends(get_db),
    _: User = Depends(require_placement_officer),
):
    q = db.query(User).filter(User.role == "student")
    if status_filter == "placed":
        q = q.filter(User.placement_status == "placed")
    elif status_filter == "unplaced":
        q = q.filter(User.placement_status == "unplaced")
    return q.order_by(User.name).all()


@router.put("/students/{student_id}/placement", response_model=StudentSummary)
def update_placement(
    student_id: int,
    payload: PlacementUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_placement_officer),
):
    student = db.query(User).filter(User.id == student_id, User.role == "student").first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if payload.placement_status not in ("placed", "unplaced"):
        raise HTTPException(status_code=400, detail="Invalid placement status")
    student.placement_status = payload.placement_status
    student.placed_company_id = payload.placed_company_id if payload.placement_status == "placed" else None
    db.commit()
    db.refresh(student)
    return student


@router.post("/companies", response_model=CompanyOut)
def create_company(
    payload: CompanyCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_placement_officer),
):
    if db.query(Company).filter(Company.name == payload.name).first():
        raise HTTPException(status_code=400, detail="Company with this name already exists")
    company = Company(**payload.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.put("/companies/{company_id}", response_model=CompanyOut)
def update_company(
    company_id: int,
    payload: CompanyUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_placement_officer),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(company, k, v)
    db.commit()
    db.refresh(company)
    return company


@router.delete("/companies/{company_id}")
def delete_company(
    company_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_placement_officer),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(company)
    db.commit()
    return {"deleted": True}