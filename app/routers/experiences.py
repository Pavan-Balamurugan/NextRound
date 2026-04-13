from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db, get_current_user
from app.models import Experience, User
from app.schemas import ExperienceCreate, ExperienceOut

router = APIRouter(prefix="/api/experiences", tags=["experiences"])


@router.get("", response_model=List[ExperienceOut])
def list_experiences(company_id: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(Experience)
    if company_id:
        q = q.filter(Experience.company_id == company_id)
    return q.order_by(Experience.created_at.desc()).all()


@router.post("", response_model=ExperienceOut)
def create_experience(
    payload: ExperienceCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    exp = Experience(user_id=current.id, **payload.model_dump())
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return exp


@router.get("/{exp_id}", response_model=ExperienceOut)
def get_experience(exp_id: int, db: Session = Depends(get_db)):
    exp = db.query(Experience).filter(Experience.id == exp_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experience not found")
    return exp
