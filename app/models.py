from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="student")  # student | alumni | placement_officer
    cgpa = Column(Float, default=0.0)
    department = Column(String, default="CS")
    year = Column(Integer, default=3)
    skills = Column(JSON, default=list)
    target_companies = Column(JSON, default=list)
    resume_data = Column(JSON, nullable=True, default=None)
    placement_status = Column(String, default="unplaced")  # unplaced | placed
    placed_company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    # Streak / consistency tracking
    last_login_date = Column(String, nullable=True, default=None)   # ISO date "YYYY-MM-DD"
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    login_history = Column(JSON, default=list)  # list of "YYYY-MM-DD" strings (last 30 days)
    last_challenge_date = Column(String, nullable=True, default=None)  # ISO date of last solved challenge

    experiences = relationship("Experience", back_populates="user", cascade="all, delete-orphan")
    study_plans = relationship("StudyPlan", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    placed_company = relationship("Company", foreign_keys=[placed_company_id])

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    sector = Column(String)
    ctc_min = Column(Float)
    ctc_max = Column(Float)
    eligibility_cgpa = Column(Float)
    difficulty = Column(String)  # easy | medium | hard
    rounds = Column(JSON, default=list)
    topics = Column(JSON, default=list)
    description = Column(Text)

    experiences = relationship("Experience", back_populates="company", cascade="all, delete-orphan")


class Experience(Base):
    __tablename__ = "experiences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    company_id = Column(Integer, ForeignKey("companies.id"))
    role = Column(String)
    verdict = Column(String)  # selected | rejected
    year = Column(Integer)
    rounds_description = Column(Text)
    tips = Column(Text)
    difficulty_rating = Column(Integer, default=3)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="experiences")
    company = relationship("Company", back_populates="experiences")


class StudyPlan(Base):
    __tablename__ = "study_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    company_id = Column(Integer, ForeignKey("companies.id"))
    plan_json = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="study_plans")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String)  # user | assistant
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chat_messages")