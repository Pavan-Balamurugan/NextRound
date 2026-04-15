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
from app.routers.streak import _compute_consistency

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
    weeks = max(2, min(12, payload.weeks or 4))  # clamp 2–12 weeks
    plan = ai_service.generate_study_plan(current, company, experiences, weeks=weeks)
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
    result = ai_service.generate_readiness_score(current, company, experiences)

    # Blend: 70% AI score + 30% consistency score
    consistency = _compute_consistency(current.login_history or [])
    raw_ai = result["score"]
    blended = round(0.7 * raw_ai + 0.3 * consistency)
    result["score"] = blended
    result.setdefault("strengths", [])
    result.setdefault("gaps", [])
    result.setdefault("action_items", [])

    # Add consistency context to strengths/gaps
    if consistency >= 60:
        result["strengths"].insert(0, f"🔥 {current.current_streak or 0}-day login streak — great consistency!")
    elif consistency >= 30:
        result["action_items"].insert(0, f"📅 Consistency score: {consistency}/100 — log in daily to boost your score")
    else:
        result["gaps"].insert(0, f"📅 Low consistency ({consistency}/100) — daily logins raise your readiness by up to 30 pts")

    return result


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