"""Wipe + reseed the database. Run: python -m app.seed"""
from app.database import Base, engine, SessionLocal
from app.models import User, Company, Experience, StudyPlan, ChatMessage
from app.services.auth_service import hash_password


def run():
    print("🌱 Dropping and recreating tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # ---------- Users ----------
        arya = User(
            name="Arya Stark",
            email="arya@valyrian.dev",
            password_hash=hash_password("password123"),
            role="student",
            cgpa=8.2,
            department="CS",
            year=3,
            skills=["Python", "SQL", "React"],
            target_companies=[],
        )
        jon = User(
            name="Jon Snow",
            email="jon@valyrian.dev",
            password_hash=hash_password("password123"),
            role="alumni",
            cgpa=8.7,
            department="CS",
            year=4,
            skills=["Java", "Spring Boot", "AWS", "System Design"],
            target_companies=[],
        )
        db.add_all([arya, jon])
        db.commit()

        # ---------- Companies ----------
        companies_data = [
            dict(
                name="TCS Digital",
                sector="IT Services",
                ctc_min=7.0, ctc_max=9.0, eligibility_cgpa=6.5, difficulty="easy",
                rounds=["Online Test", "Technical Interview", "HR Interview"],
                topics=["C/C++", "DBMS", "OS", "Aptitude", "Basic DSA"],
                description="TCS Digital hires for premium roles via the National Qualifier Test. Known for moderate difficulty and fair process.",
            ),
            dict(
                name="Infosys",
                sector="IT Services",
                ctc_min=6.5, ctc_max=8.0, eligibility_cgpa=6.0, difficulty="easy",
                rounds=["InfyTQ", "Technical Interview", "HR"],
                topics=["Java", "DBMS", "Python", "Aptitude"],
                description="Infosys recruits through InfyTQ with strong emphasis on fundamentals and communication.",
            ),
            dict(
                name="Wipro",
                sector="IT Services",
                ctc_min=6.5, ctc_max=7.5, eligibility_cgpa=6.0, difficulty="easy",
                rounds=["Elite NTH", "Technical", "HR"],
                topics=["C", "OOP", "DBMS", "English"],
                description="Wipro's Elite program is a reliable entry for tier-2/3 college students with good fundamentals.",
            ),
            dict(
                name="Cognizant",
                sector="IT Services",
                ctc_min=6.75, ctc_max=9.0, eligibility_cgpa=6.0, difficulty="easy",
                rounds=["Aptitude", "Coding", "Technical + HR"],
                topics=["DSA", "SQL", "OOP", "Aptitude"],
                description="Cognizant GenC and GenC Next programs hire at scale during campus season.",
            ),
            dict(
                name="Accenture",
                sector="Consulting/IT",
                ctc_min=4.5, ctc_max=11.5, eligibility_cgpa=6.0, difficulty="easy",
                rounds=["Cognitive & Technical Assessment", "Coding", "Interview"],
                topics=["MS Office fundamentals", "Coding basics", "Communication", "Pseudo-code"],
                description="Accenture offers both Associate and Advanced Associate roles with different CTC tiers.",
            ),
            dict(
                name="Zoho",
                sector="Product",
                ctc_min=7.5, ctc_max=12.5, eligibility_cgpa=6.5, difficulty="medium",
                rounds=["Written Test", "Programming Round", "Advanced Programming", "Technical", "HR"],
                topics=["C/C++", "DSA", "Puzzles", "OOP", "Debugging"],
                description="Zoho's famous 5-round interview process is legendary — tests real problem solving over memorization.",
            ),
            dict(
                name="Freshworks",
                sector="Product",
                ctc_min=9.0, ctc_max=14.0, eligibility_cgpa=7.0, difficulty="medium",
                rounds=["Online Test", "Coding Round", "Technical", "HR"],
                topics=["DSA", "System Design basics", "Ruby/Python", "DBMS"],
                description="Freshworks hires strong full-stack engineers with emphasis on clean code and product thinking.",
            ),
            dict(
                name="Amazon",
                sector="Product/Cloud",
                ctc_min=22.0, ctc_max=32.0, eligibility_cgpa=7.0, difficulty="hard",
                rounds=["Online Assessment", "Technical 1", "Technical 2", "Bar Raiser", "HR"],
                topics=["DSA", "System Design", "OOP", "Leadership Principles", "OS/DBMS"],
                description="Amazon SDE hiring is rigorous — expect hard DSA and explicit mapping to the 16 Leadership Principles.",
            ),
            dict(
                name="Microsoft",
                sector="Product",
                ctc_min=28.0, ctc_max=45.0, eligibility_cgpa=7.5, difficulty="hard",
                rounds=["Online Assessment", "Group Coding", "Technical 1", "Technical 2", "AA Round"],
                topics=["DSA", "System Design", "OS", "CN", "Problem Solving"],
                description="Microsoft's IDC hiring process focuses deeply on DSA and design thinking with an As-Appropriate final round.",
            ),
            dict(
                name="Goldman Sachs",
                sector="Finance/Tech",
                ctc_min=25.0, ctc_max=35.0, eligibility_cgpa=7.5, difficulty="hard",
                rounds=["CoderPad Test", "Technical 1", "Technical 2", "HireVue", "Superday"],
                topics=["DSA", "OOP", "DBMS", "Finance basics", "System Design"],
                description="Goldman hires technology analysts across engineering divisions — strong DSA and clear communication win.",
            ),
        ]
        company_objs = [Company(**c) for c in companies_data]
        db.add_all(company_objs)
        db.commit()

        by_name = {c.name: c for c in company_objs}
        arya.target_companies = [by_name["Amazon"].id, by_name["Zoho"].id, by_name["Freshworks"].id]
        db.commit()

        # ---------- Experiences ----------
        experiences_data = [
            ("TCS Digital", "selected", 2024, "Online test had 20 aptitude + 2 coding questions. Interview focused on my final-year project and basic DBMS joins. HR was conversational about relocation.",
             "Revise your projects deeply and stay calm — they value clarity over brilliance.", 2),
            ("TCS Digital", "selected", 2023, "Test was easy but time pressured. Technical asked OOP pillars, SQL query on employee table, and one C output question.",
             "Don't skip aptitude prep — it's the real filter.", 2),
            ("Infosys", "selected", 2024, "InfyTQ certification helped me skip the MCQ round. Tech interview asked about normalization and a simple string reversal in Java.",
             "Get the InfyTQ certificate early — it's a genuine shortcut.", 2),
            ("Wipro", "rejected", 2024, "Cleared the written but stumbled on a linked list question in the technical round. HR never happened.",
             "Practice linked-list and pointer manipulation — they ask it every single year.", 3),
            ("Cognizant", "selected", 2024, "Aptitude was standard. Coding had one easy array question. Technical was mostly SQL joins and project discussion.",
             "SQL joins + your own project = 80% of the interview.", 2),
            ("Accenture", "selected", 2023, "Cognitive was easy, coding had pseudo-code MCQs. Interview asked 'Tell me about yourself' and one tech question on OOP.",
             "Focus on communication — they weight soft skills heavily.", 1),
            ("Zoho", "selected", 2024, "Round 1 was 20 C output questions. Round 2 had 3 programs (string, pattern, simple DP). Round 3 was a machine-coding debugging task — super unique.",
             "Practice on paper and pen — no IDE allowed in early rounds.", 4),
            ("Zoho", "rejected", 2023, "Cleared 3 rounds but failed the advanced programming round where I had to build a mini library management system in 2 hours.",
             "Practice full problem design, not just DSA snippets.", 4),
            ("Freshworks", "selected", 2024, "OA had 2 medium DSA problems. Technical interviews were deeply about system design and how I'd scale my college project.",
             "Think out loud — interviewers actively coach you through.", 4),
            ("Amazon", "selected", 2024, "OA had 2 hard DSA (graph + DP). Three technical rounds all mapped to leadership principles. Bar raiser grilled me on ambiguity handling.",
             "Prepare 6 STAR stories mapped to LPs — it's non-negotiable.", 5),
            ("Amazon", "rejected", 2023, "Cleared OA and first technical but failed on a system design followup about a rate limiter. DSA was fine.",
             "Don't ignore LLD/system design even at SDE-1 level.", 5),
            ("Microsoft", "selected", 2024, "OA was 3 DSA problems in 90 min. Group coding round was surprising — collaborate with 2 others to solve a graph problem. AA round asked about OS scheduling in depth.",
             "Revise OS and CN thoroughly — they love fundamentals.", 5),
            ("Microsoft", "rejected", 2024, "Stuck on a tree DP problem in technical 2. Interviewer was kind but time ran out.",
             "Tree recursion with memoization — practice until it's automatic.", 5),
            ("Goldman Sachs", "selected", 2023, "CoderPad had 2 medium questions. Technical rounds went deep on hashmaps and one system design (design a stock ticker). Superday was 4 back-to-back interviews.",
             "Know your resume cold — every line can be interrogated.", 5),
            ("Goldman Sachs", "rejected", 2024, "Failed HireVue due to weak behavioral answers despite clearing technical rounds.",
             "Don't underestimate HireVue — rehearse answers out loud.", 4),
        ]

        for cname, verdict, year, rd, tip, rating in experiences_data:
            db.add(
                Experience(
                    user_id=jon.id,
                    company_id=by_name[cname].id,
                    role="SDE Intern" if year >= 2024 else "Software Engineer",
                    verdict=verdict,
                    year=year,
                    rounds_description=rd,
                    tips=tip,
                    difficulty_rating=rating,
                )
            )
        db.commit()

        print(f"✅ Seeded {db.query(User).count()} users, {db.query(Company).count()} companies, {db.query(Experience).count()} experiences.")
        print("   Login: arya@valyrian.dev / password123")
    finally:
        db.close()


if __name__ == "__main__":
    run()
