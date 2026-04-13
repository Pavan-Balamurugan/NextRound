import json
from typing import List, Optional

from app.config import settings

DEMO_MODE = settings.demo_mode

_model = None

if DEMO_MODE:
    print("⚠️  [DEMO MODE] Gemini API key not configured — using canned responses.")
else:
    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.GEMINI_API_KEY)
        _model = genai.GenerativeModel("gemini-2.0-flash")
        print("✅ Gemini live mode enabled (gemini-2.0-flash).")
    except Exception as e:
        print(f"⚠️  [DEMO MODE] Failed to init Gemini ({e}) — falling back to canned responses.")
        DEMO_MODE = True


# ---------- Demo canned responses ----------
def _demo_study_plan(company_name: str) -> dict:
    return {
        "weeks": [
            {
                "week_number": 1,
                "focus": "Core DSA foundations",
                "topics": ["Arrays", "Strings", "Hashing", "Two Pointers"],
                "resources": ["NeetCode 150 — Arrays section", "Striver SDE Sheet Day 1-3"],
                "practice_goal": "Solve 20 easy + 10 medium problems",
            },
            {
                "week_number": 2,
                "focus": "Trees, Recursion & DP warm-up",
                "topics": ["Binary Trees", "BST", "Recursion", "1D DP"],
                "resources": ["Striver Tree Playlist", "GfG Top 50 DP"],
                "practice_goal": "Complete 15 tree problems + 8 DP problems",
            },
            {
                "week_number": 3,
                "focus": f"{company_name} specifics + System Design basics",
                "topics": ["Graphs", "Sliding Window", "LLD basics", "OOP"],
                "resources": [f"{company_name} tagged problems on LeetCode", "Gaurav Sen LLD intro"],
                "practice_goal": "Mock interview 2x with peer",
            },
            {
                "week_number": 4,
                "focus": "Mock interviews + CS fundamentals revision",
                "topics": ["OS", "DBMS", "CN", "Project deep-dive"],
                "resources": ["Love Babbar CS fundamentals", "InterviewBit CS"],
                "practice_goal": "3 full mock rounds, revise resume projects",
            },
        ]
    }


def _demo_readiness(company_name: str) -> dict:
    return {
        "score": 72,
        "strengths": [
            "Strong Python and SQL foundation",
            "Relevant React project experience",
            "CGPA comfortably above eligibility cutoff",
        ],
        "gaps": [
            "Limited exposure to system design",
            "Graph and DP problems need more practice",
            f"No {company_name}-tagged problems solved yet",
        ],
        "action_items": [
            f"Solve 30 {company_name}-tagged problems on LeetCode",
            "Do 2 mock system design rounds this week",
            "Revise OS + DBMS fundamentals from notes",
            "Prepare 2 STAR-format project stories",
        ],
    }


def _demo_chat(message: str, company_name: Optional[str]) -> str:
    tag = f" for **{company_name}**" if company_name else ""
    return (
        f"Great question! Based on senior experiences{tag}, here's what I'd suggest:\n\n"
        f"1. Focus on DSA fundamentals first — arrays, strings, and trees dominate first rounds.\n"
        f"2. Seniors consistently mention that clean communication during the coding round matters as much as the solution.\n"
        f"3. Practice 2–3 problems daily and do at least one timed mock per week.\n\n"
        f"You've got this — the fact that you're preparing early already puts you ahead. 💪\n\n"
        f"_(Demo mode reply — add a real GEMINI_API_KEY in .env for personalized grounded answers.)_"
    )


# ---------- Live helpers ----------
STUDY_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "weeks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "week_number": {"type": "integer"},
                    "focus": {"type": "string"},
                    "topics": {"type": "array", "items": {"type": "string"}},
                    "resources": {"type": "array", "items": {"type": "string"}},
                    "practice_goal": {"type": "string"},
                },
                "required": ["week_number", "focus", "topics", "resources", "practice_goal"],
            },
        }
    },
    "required": ["weeks"],
}

READINESS_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "integer"},
        "strengths": {"type": "array", "items": {"type": "string"}},
        "gaps": {"type": "array", "items": {"type": "string"}},
        "action_items": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["score", "strengths", "gaps", "action_items"],
}


def _context_block(user, company, experiences) -> str:
    exp_text = "\n\n".join(
        [
            f"- Senior ({e.verdict}, {e.year}, rating {e.difficulty_rating}/5): {e.rounds_description}\n  Tip: {e.tips}"
            for e in experiences
        ]
    ) or "No senior experiences on record yet."

    return (
        f"STUDENT PROFILE:\n"
        f"- Name: {user.name}, Year {user.year} {user.department}, CGPA {user.cgpa}\n"
        f"- Skills: {', '.join(user.skills or [])}\n\n"
        f"TARGET COMPANY: {company.name} ({company.sector})\n"
        f"- CTC: {company.ctc_min}-{company.ctc_max} LPA | Eligibility CGPA: {company.eligibility_cgpa}\n"
        f"- Difficulty: {company.difficulty}\n"
        f"- Rounds: {', '.join(company.rounds or [])}\n"
        f"- Topics: {', '.join(company.topics or [])}\n\n"
        f"RECENT SENIOR EXPERIENCES:\n{exp_text}\n"
    )


# ---------- Public API ----------
def generate_study_plan(user, company, experiences) -> dict:
    if DEMO_MODE:
        return _demo_study_plan(company.name)
    try:
        import google.generativeai as genai

        ctx = _context_block(user, company, experiences)
        prompt = (
            "Create a 4-week personalized placement prep plan grounded in the senior experiences "
            "below. Tailor it to the student's skills and the company's rounds/topics.\n\n" + ctx
        )
        model = genai.GenerativeModel(
            "gemini-2.0-flash",
            system_instruction="You are an expert campus placement coach for Indian engineering students.",
        )
        resp = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": STUDY_PLAN_SCHEMA,
                "temperature": 0.7,
            },
        )
        return json.loads(resp.text)
    except Exception as e:
        print(f"[AI] study_plan fallback due to error: {e}")
        return _demo_study_plan(company.name)


def generate_readiness_score(user, company, experiences) -> dict:
    if DEMO_MODE:
        return _demo_readiness(company.name)
    try:
        import google.generativeai as genai

        ctx = _context_block(user, company, experiences)
        prompt = (
            "Assess this student's readiness for the target company. Score 0-100. "
            "Be honest and specific — ground gaps in the senior experiences provided.\n\n" + ctx
        )
        model = genai.GenerativeModel(
            "gemini-2.0-flash",
            system_instruction="You are a strict but encouraging placement mentor.",
        )
        resp = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": READINESS_SCHEMA,
                "temperature": 0.4,
            },
        )
        return json.loads(resp.text)
    except Exception as e:
        print(f"[AI] readiness fallback due to error: {e}")
        return _demo_readiness(company.name)


def chat(user, company, experiences, message: str) -> str:
    company_name = company.name if company else None
    if DEMO_MODE:
        return _demo_chat(message, company_name)
    try:
        import google.generativeai as genai

        system_prompt = (
            "You are helping a student prepare for campus placements at an Indian engineering "
            "college. Ground your answer in the senior experiences provided below. Be specific, "
            "actionable, and warm."
        )
        ctx = _context_block(user, company, experiences) if company else f"STUDENT: {user.name}, skills: {user.skills}"
        model = genai.GenerativeModel("gemini-2.0-flash", system_instruction=system_prompt)
        resp = model.generate_content(
            f"{ctx}\n\nSTUDENT QUESTION: {message}",
            generation_config={"temperature": 0.8, "max_output_tokens": 800},
        )
        return resp.text
    except Exception as e:
        print(f"[AI] chat fallback due to error: {e}")
        return _demo_chat(message, company_name)
