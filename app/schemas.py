from datetime import datetime
from typing import List, Optional, Any

from pydantic import BaseModel, EmailStr, ConfigDict


# ---------- Auth ----------
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "student"
    cgpa: float = 0.0
    department: str = "CS"
    year: int = 3
    skills: List[str] = []
    target_companies: List[int] = []


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr
    role: str
    cgpa: float
    department: str
    year: int
    skills: List[str] = []
    target_companies: List[int] = []


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    cgpa: Optional[float] = None
    department: Optional[str] = None
    year: Optional[int] = None
    skills: Optional[List[str]] = None
    target_companies: Optional[List[int]] = None


# ---------- Company ----------
class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    sector: Optional[str]
    ctc_min: Optional[float]
    ctc_max: Optional[float]
    eligibility_cgpa: Optional[float]
    difficulty: Optional[str]
    rounds: List[str] = []
    topics: List[str] = []
    description: Optional[str] = ""


# ---------- Experience ----------
class ExperienceCreate(BaseModel):
    company_id: int
    role: str
    verdict: str
    year: int
    rounds_description: str
    tips: str
    difficulty_rating: int = 3


class ExperienceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    company_id: int
    role: str
    verdict: str
    year: int
    rounds_description: str
    tips: str
    difficulty_rating: int
    created_at: datetime


class CompanyDetail(CompanyOut):
    experiences: List[ExperienceOut] = []


# ---------- AI ----------
class AIRequest(BaseModel):
    company_id: int


class ChatRequest(BaseModel):
    message: str
    company_id: Optional[int] = None


class ChatResponse(BaseModel):
    reply: str


class StudyPlanResponse(BaseModel):
    weeks: List[dict]


class ReadinessResponse(BaseModel):
    score: int
    strengths: List[str]
    gaps: List[str]
    action_items: List[str]


class HealthResponse(BaseModel):
    demo_mode: bool
    status: str = "ok"

class ResumeExtractResponse(BaseModel):
    skills: List[str] = []
    projects: List[str] = []
    certifications: List[str] = []
    education: List[str] = []
    experience: List[str] = []
    summary: str = ""

class ResumeUploadResponse(BaseModel):
    extracted: ResumeExtractResponse
    skills_added: int
    message: str