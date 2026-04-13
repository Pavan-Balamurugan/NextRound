import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db, get_current_user
from app.models import Company, Experience, StudyPlan, ChatMessage, User
from app.schemas import (
    AIRequest,
    ChatRequest,
    ChatResponse,
    StudyPlanResponse,
    ReadinessResponse,
)
from app.services import ai_service

router = APIRouter(prefix="/api/ai", tags=["ai"])


def _load_context(db: Session, company_id: int):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    experiences = (
        db.query(Experience)
        .filter(Experience.company_id == company_id)
        .order_by(Experience.created_at.desc())
        .limit(3)
        .all()
    )
    return company, experiences


@router.post("/study-plan", response_model=StudyPlanResponse)
def study_plan(
    payload: AIRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    company, experiences = _load_context(db, payload.company_id)
    plan = ai_service.generate_study_plan(current, company, experiences)
    db.add(
        StudyPlan(
            user_id=current.id,
            company_id=company.id,
            plan_json=json.dumps(plan),
        )
    )
    db.commit()
    return plan


@router.post("/readiness-score", response_model=ReadinessResponse)
def readiness_score(
    payload: AIRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    company, experiences = _load_context(db, payload.company_id)
    return ai_service.generate_readiness_score(current, company, experiences)


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    company, experiences = (None, [])
    if payload.company_id:
        company, experiences = _load_context(db, payload.company_id)

    db.add(ChatMessage(user_id=current.id, role="user", content=payload.message))
    reply = ai_service.chat(current, company, experiences, payload.message)
    db.add(ChatMessage(user_id=current.id, role="assistant", content=reply))
    db.commit()
    return ChatResponse(reply=reply)
