from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from pypdf import PdfReader
import io

from app.deps import get_db, get_current_user
from app.models import User
from app.schemas import ResumeUploadResponse, ResumeExtractResponse
from app.services.ai_service import extract_resume

router = APIRouter(prefix="/api/resume", tags=["resume"])


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    # Validate
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5 MB)")

    # Extract text from PDF
    try:
        reader = PdfReader(io.BytesIO(contents))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read PDF: {e}")

    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="Could not extract text — is this a scanned PDF? Try a text-based resume.",
        )

    # AI extraction
    extracted = extract_resume(text)

    # Merge skills into user profile (dedup, preserve existing)
    existing_skills = set(s.strip() for s in (current.skills or []))
    new_skills = set(s.strip() for s in extracted.get("skills", []) if s.strip())
    merged = sorted(existing_skills | new_skills, key=str.lower)
    skills_added = len(merged) - len(existing_skills)

    current.skills = merged
    current.resume_data = extracted
    db.commit()
    db.refresh(current)

    return ResumeUploadResponse(
        extracted=ResumeExtractResponse(**extracted),
        skills_added=skills_added,
        message=f"Resume parsed successfully. {skills_added} new skill(s) added to your profile.",
    )