import json
from typing import List, Optional

from app.config import settings

DEMO_MODE = settings.demo_mode

_client = None
MODEL_NAME = "llama-3.3-70b-versatile"

if DEMO_MODE:
    print("⚠️  [DEMO MODE] Groq API key not configured — using canned responses.")
else:
    try:
        from groq import Groq

        _client = Groq(api_key=settings.GROQ_API_KEY)
        print(f"✅ Groq live mode enabled ({MODEL_NAME}).")
    except Exception as e:
        print(f"⚠️  [DEMO MODE] Failed to init Groq ({e}) — falling back to canned responses.")
        DEMO_MODE = True


# ---------- Demo canned responses ----------
def _demo_study_plan(company_name: str, weeks: int = 4) -> dict:
    week_templates = [
        {
            "focus": "Core DSA foundations",
            "topics": ["Arrays", "Strings", "Hashing", "Two Pointers"],
            "resources": ["NeetCode 150 — Arrays section", "Striver SDE Sheet Day 1-3"],
            "practice_goal": "Solve 20 easy + 10 medium problems",
        },
        {
            "focus": "Trees, Recursion & DP warm-up",
            "topics": ["Binary Trees", "BST", "Recursion", "1D DP"],
            "resources": ["Striver Tree Playlist", "GfG Top 50 DP"],
            "practice_goal": "Complete 15 tree problems + 8 DP problems",
        },
        {
            "focus": f"{company_name} specifics + System Design basics",
            "topics": ["Graphs", "Sliding Window", "LLD basics", "OOP"],
            "resources": [f"{company_name} tagged problems on LeetCode", "Gaurav Sen LLD intro"],
            "practice_goal": "Mock interview 2x with peer",
        },
        {
            "focus": "Mock interviews + CS fundamentals revision",
            "topics": ["OS", "DBMS", "CN", "Project deep-dive"],
            "resources": ["Love Babbar CS fundamentals", "InterviewBit CS"],
            "practice_goal": "3 full mock rounds, revise resume projects",
        },
        {
            "focus": "Advanced DSA — Graphs & DP",
            "topics": ["Graph algorithms", "2D DP", "Tries", "Segment Trees"],
            "resources": ["Striver Graph Series", "Aditya Verma DP playlist"],
            "practice_goal": "Solve 20 medium/hard graph + DP problems",
        },
        {
            "focus": "System Design deep-dive",
            "topics": ["HLD basics", "Scalability", "Databases", "Caching"],
            "resources": ["Gaurav Sen System Design", "Grokking the System Design Interview"],
            "practice_goal": "Design 4 systems end-to-end (URL shortener, LRU cache, etc.)",
        },
        {
            "focus": "Behavioural + Project prep",
            "topics": ["STAR method", "Leadership stories", "Resume deep-dive", "HR rounds"],
            "resources": ["Jeff H Sipe YouTube", "Pramp for mock interviews"],
            "practice_goal": "Prepare 6 STAR stories, rehearse project explanations 3x",
        },
        {
            "focus": "Full mock sprints + final polish",
            "topics": ["Mixed DSA", "System Design mock", "HR simulation", "Company-specific research"],
            "resources": ["Pramp", "Interviewing.io", f"{company_name} Glassdoor reviews"],
            "practice_goal": "5 full mock rounds, solve 10 company-tagged problems",
        },
    ]

    # Cycle through templates to fill requested weeks
    result_weeks = []
    for i in range(weeks):
        tmpl = week_templates[i % len(week_templates)].copy()
        tmpl["week_number"] = i + 1
        result_weeks.append(tmpl)

    return {"weeks": result_weeks}


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
        f"_(Demo mode reply — add a real GROQ_API_KEY in .env for personalized grounded answers.)_"
    )


# ---------- Context builder ----------
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


# ---------- Groq helpers ----------
def _groq_json(system: str, user_msg: str, temperature: float = 0.7) -> dict:
    """Call Groq with JSON mode, return parsed dict."""
    resp = _client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": system + "\n\nIMPORTANT: Respond ONLY with valid JSON. No markdown fences, no explanations.",
            },
            {"role": "user", "content": user_msg},
        ],
        response_format={"type": "json_object"},
        temperature=temperature,
        max_tokens=2048,
    )
    return json.loads(resp.choices[0].message.content)


def _groq_text(system: str, user_msg: str, temperature: float = 0.8, max_tokens: int = 800) -> str:
    """Call Groq for a plain text reply."""
    resp = _client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content


# ---------- Public API ----------
def generate_study_plan(user, company, experiences, weeks: int = 4) -> dict:
    weeks = max(2, min(12, weeks))  # safety clamp
    if DEMO_MODE:
        return _demo_study_plan(company.name, weeks=weeks)
    try:
        ctx = _context_block(user, company, experiences)
        system = (
            "You are an expert campus placement coach for Indian engineering students. "
            "You create personalized study plans grounded in real senior experiences."
        )
        user_msg = (
            f"Create a {weeks}-week personalized placement prep plan grounded in the senior "
            "experiences below. Tailor it to the student's skills and the company's rounds/topics. "
            f"The plan MUST have exactly {weeks} weeks — no more, no less.\n\n"
            f"{ctx}\n\n"
            'Return JSON in this EXACT shape: {"weeks": [{"week_number": 1, "focus": "...", '
            '"topics": ["..."], "resources": ["..."], "practice_goal": "..."}, ...]}. '
            f"Include exactly {weeks} weeks."
        )
        result = _groq_json(system, user_msg, temperature=0.7)
        if "weeks" not in result or not isinstance(result["weeks"], list):
            raise ValueError("Invalid plan shape from model")
        # Ensure correct week count (model sometimes disobeys)
        if len(result["weeks"]) != weeks:
            raise ValueError(f"Model returned {len(result['weeks'])} weeks, expected {weeks}")
        return result
    except Exception as e:
        print(f"[AI] study_plan fallback due to error: {e}")
        return _demo_study_plan(company.name, weeks=weeks)


def generate_readiness_score(user, company, experiences) -> dict:
    if DEMO_MODE:
        return _demo_readiness(company.name)
    try:
        ctx = _context_block(user, company, experiences)
        system = (
            "You are a strict but encouraging placement mentor. You assess a student's readiness "
            "for a specific company honestly, grounded in evidence from senior experiences."
        )
        user_msg = (
            "Assess this student's readiness for the target company. Score 0-100. "
            "Be honest and specific — ground gaps in the senior experiences provided.\n\n"
            f"{ctx}\n\n"
            'Return JSON in this EXACT shape: {"score": <int 0-100>, "strengths": ["..."], '
            '"gaps": ["..."], "action_items": ["..."]}. Each list should have 3-5 items.'
        )
        result = _groq_json(system, user_msg, temperature=0.4)
        if "score" not in result:
            raise ValueError("Missing score in response")
        result["score"] = int(result["score"])
        for k in ("strengths", "gaps", "action_items"):
            if k not in result or not isinstance(result[k], list):
                result[k] = []
        return result
    except Exception as e:
        print(f"[AI] readiness fallback due to error: {e}")
        return _demo_readiness(company.name)


def chat(user, company, experiences, message: str) -> str:
    company_name = company.name if company else None
    if DEMO_MODE:
        return _demo_chat(message, company_name)
    try:
        system_prompt = (
            "You are helping a student prepare for campus placements at an Indian engineering "
            "college. Ground your answer in the senior experiences provided below. Be specific, "
            "actionable, and warm. Keep responses focused (2-4 short paragraphs)."
        )
        if company:
            ctx = _context_block(user, company, experiences)
        else:
            ctx = (
                f"STUDENT PROFILE:\n- Name: {user.name}, Year {user.year} {user.department}, "
                f"CGPA {user.cgpa}\n- Skills: {', '.join(user.skills or [])}\n"
            )
        user_msg = f"{ctx}\n\nSTUDENT QUESTION: {message}"
        return _groq_text(system_prompt, user_msg, temperature=0.8, max_tokens=800)
    except Exception as e:
        print(f"[AI] chat fallback due to error: {e}")
        return _demo_chat(message, company_name)
    

# ---------- Resume extraction ----------
RESUME_SCHEMA_HINT = (
    'Return JSON in this EXACT shape: {'
    '"skills": ["..."], '
    '"projects": ["short one-line descriptions"], '
    '"certifications": ["..."], '
    '"education": ["degree + institution + year"], '
    '"experience": ["role + company + duration"], '
    '"summary": "one-sentence professional summary"'
    '}'
)

def _demo_resume() -> dict:
    return {
        "skills": ["Python", "FastAPI", "SQL", "React", "Git", "REST APIs"],
        "projects": [
            "Placement prep platform with AI integration",
            "Expense tracker web app with React frontend",
        ],
        "certifications": ["AWS Cloud Practitioner"],
        "education": ["B.E. Computer Science, Your College, 2023-2027"],
        "experience": ["Summer Intern, TechCorp, 2 months"],
        "summary": "Third-year CS student with full-stack development experience.",
    }

def extract_resume(resume_text: str) -> dict:
    """Extract structured data from resume text using AI."""
    if DEMO_MODE:
        return _demo_resume()
    try:
        system = (
            "You are a resume parser. Extract structured data from the resume text provided. "
            "Infer skills from projects and experience sections too — not just explicit skill lists. "
            "Be concise. Keep each list item short."
        )
        user_msg = (
            f"Parse this resume and extract key information.\n\n"
            f"RESUME TEXT:\n{resume_text[:8000]}\n\n"
            f"{RESUME_SCHEMA_HINT}"
        )
        result = _groq_json(system, user_msg, temperature=0.2)
        for key in ("skills", "projects", "certifications", "education", "experience"):
            if key not in result or not isinstance(result[key], list):
                result[key] = []
        if "summary" not in result:
            result["summary"] = ""
        return result
    except Exception as e:
        print(f"[AI] resume extract fallback due to error: {e}")
        return _demo_resume()