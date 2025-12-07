import math
from sqlalchemy.orm import Session
from sqlalchemy import text

from models import Job
from schemas import SurveySchema


# ---------------------------------------------------------
# USER PROFILE CONSTRUCTION FROM SURVEY ANSWERS
# ---------------------------------------------------------
def _estimate_user_profile(data: SurveySchema):
    """
    Convert survey answers into a numerical profile that can be compared
    against O*NET job profiles.
    """

    # Core dimensions — 1–5 scale
    data_pref = (data.q1 + data.q11) / 2              # analytical / data skills
    tech_interest = (data.q2 + data.q4 + data.q12) / 3 # tech comfort + emerging tech interest
    comm = (data.q13 + (5 if data.q5 == "team" else 3)) / 2
    stability = data.q6
    salary = data.q10
    remote = data.q9
    focus_pref = data.q7  # chosen role type

    # Rough RIASEC from main survey (Q1–Q15)
    realistic_est = data.q15
    investigative_est = data.q1
    artistic_est = 3
    social_est = 5 if data.q5 == "team" else 3
    enterprising_est = data.q14
    conventional_est = 5 if data.q3 == "structured" else 3

    riasec_estimated = (
        realistic_est,
        investigative_est,
        artistic_est,
        social_est,
        enterprising_est,
        conventional_est,
    )

    # RIASEC from explicit personality items (Q16–Q21)
    realistic_custom = data.r1
    investigative_custom = data.i1
    artistic_custom = data.a1
    social_custom = data.s1
    enterprising_custom = data.e1
    conventional_custom = data.c1

    riasec_custom = (
        realistic_custom,
        investigative_custom,
        artistic_custom,
        social_custom,
        enterprising_custom,
        conventional_custom,
    )

    return {
        "data_pref": data_pref,
        "tech_interest": tech_interest,
        "comm": comm,
        "stability": stability,
        "salary": salary,
        "remote": remote,
        "focus_pref": focus_pref,
        "riasec_estimated": riasec_estimated,
        "riasec_custom": riasec_custom,
    }


# ---------------------------------------------------------
# VECTOR SIMILARITY (RIASEC)
# ---------------------------------------------------------
def _cosine_similarity(v1, v2):
    """Return cosine similarity between two vectors."""
    if any(x is None for x in v1) or any(x is None for x in v2):
        return 0.0

    dot = sum(a * b for a, b in zip(v1, v2))
    mag1 = math.sqrt(sum(a * a for a in v1))
    mag2 = math.sqrt(sum(b * b for b in v2))

    if mag1 == 0 or mag2 == 0:
        return 0.0

    return dot / (mag1 * mag2)


# ---------------------------------------------------------
# LOAD O*NET SKILL/KNOWLEDGE AGGREGATES
# ---------------------------------------------------------
def get_skill_aggregates(db: Session):
    """
    Build dictionary mapping:
      soc_code -> {
        'data_skills': float,
        'people_skills': float,
        'tech_knowledge': float,
        'business_knowledge': float,
      }

    These aggregates summarize Skills.txt and Knowledge.txt into
    interpretable buckets that match survey questions.
    """

    aggregates = {}

    # Data/analytical skills
    q = db.execute(text("""
        SELECT soc_code, AVG(importance) AS avg_imp
        FROM job_skills
        WHERE LOWER(skill_name) LIKE '%analysis%'
           OR LOWER(skill_name) LIKE '%mathematics%'
           OR LOWER(skill_name) LIKE '%critical thinking%'
           OR LOWER(skill_name) LIKE '%complex problem solving%'
        GROUP BY soc_code;
    """))
    for soc, val in q:
        aggregates.setdefault(soc, {})["data_skills"] = float(val or 0)

    # People/communication skills
    q = db.execute(text("""
        SELECT soc_code, AVG(importance) AS avg_imp
        FROM job_skills
        WHERE LOWER(skill_name) LIKE '%active listening%'
           OR LOWER(skill_name) LIKE '%speaking%'
           OR LOWER(skill_name) LIKE '%coordination%'
           OR LOWER(skill_name) LIKE '%social%'
        GROUP BY soc_code;
    """))
    for soc, val in q:
        aggregates.setdefault(soc, {})["people_skills"] = float(val or 0)

    # Technical knowledge
    q = db.execute(text("""
        SELECT soc_code, AVG(importance) AS avg_imp
        FROM job_knowledge
        WHERE LOWER(knowledge_name) LIKE '%computer%'
           OR LOWER(knowledge_name) LIKE '%electronics%'
        GROUP BY soc_code;
    """))
    for soc, val in q:
        aggregates.setdefault(soc, {})["tech_knowledge"] = float(val or 0)

    # Business knowledge
    q = db.execute(text("""
        SELECT soc_code, AVG(importance) AS avg_imp
        FROM job_knowledge
        WHERE LOWER(knowledge_name) LIKE '%administration%'
           OR LOWER(knowledge_name) LIKE '%management%'
           OR LOWER(knowledge_name) LIKE '%business%'
        GROUP BY soc_code;
    """))
    for soc, val in q:
        aggregates.setdefault(soc, {})["business_knowledge"] = float(val or 0)

    return aggregates


# ---------------------------------------------------------
# SCORING A JOB AGAINST A USER PROFILE
# ---------------------------------------------------------
def _score_job_for_user(job: Job, profile: dict, skill_aggs: dict):
    """
    Higher score = better fit.
    Uses a positive baseline, reduced penalties, and
    combined RIASEC matching (estimated + explicit).
    """

    score = 10.0  # positive baseline

    # 1) Data / Tech / Communication fit
    score -= abs((job.required_data_skill or 3) - profile["data_pref"]) * 0.5
    score -= abs((job.required_tech_interest or 3) - profile["tech_interest"]) * 0.5
    score -= abs((job.required_communication or 3) - profile["comm"]) * 0.5

    # 2) Salary & stability
    score -= abs((job.stability_level or 3) - profile["stability"]) * 0.4
    score -= abs((job.salary_level or 3) - profile["salary"]) * 0.4

    # 3) Remote preference
    if profile["remote"] and job.remote_possible:
        score += 2.5

    # 4) Role match bonus
    if profile["focus_pref"] and job.focus_area:
        if profile["focus_pref"].lower() == (job.focus_area or "").lower():
            score += 3.5

    # 5) Combined RIASEC similarity
    riasec_est = profile["riasec_estimated"]
    riasec_custom = profile["riasec_custom"]

    combined_user_riasec = tuple(
        (riasec_est[i] * 0.6) + (riasec_custom[i] * 1.0)
        for i in range(6)
    )

    job_riasec = (
        job.riasec_r or 3,
        job.riasec_i or 3,
        job.riasec_a or 3,
        job.riasec_s or 3,
        job.riasec_e or 3,
        job.riasec_c or 3,
    )

    sim = _cosine_similarity(combined_user_riasec, job_riasec)
    score += sim * 8  # higher weight because interests are strong drivers

    # 6) Skills and knowledge aggregates
    job_features = skill_aggs.get(job.soc_code, {})

    def norm(x):
        return (x or 0) / 20.0  # approximate 0–100 → 0–5

    data_skill_norm = norm(job_features.get("data_skills"))
    people_skill_norm = norm(job_features.get("people_skills"))
    tech_knowledge_norm = norm(job_features.get("tech_knowledge"))
    business_knowledge_norm = norm(job_features.get("business_knowledge"))

    # Reward similarity (5 - abs(diff))
    score += (5 - abs(data_skill_norm - profile["data_pref"]))
    score += (5 - abs(people_skill_norm - profile["comm"]))
    score += (5 - abs(tech_knowledge_norm - profile["tech_interest"]))
    score += (5 - abs(business_knowledge_norm - profile["stability"]))

    # 7) Prefer master's-level jobs (Job Zone ≥ 4)
    if job.job_zone and job.job_zone >= 4:
        score += 1

    return score


# ---------------------------------------------------------
# MAP SURVEY ROLE PREFERENCE → MAJOR
# ---------------------------------------------------------
def _map_focus_to_major(focus_pref: str):
    if focus_pref == "data analysis":
        return "MS in Data Analytics"
    if focus_pref == "cybersecurity":
        return "MS in Cybersecurity"
    if focus_pref == "technology design":
        return "MS in Software Engineering / IT"
    return "MS in Information Systems"


# ---------------------------------------------------------
# MAIN ENTRYPOINT: GENERATE RECOMMENDATIONS
# ---------------------------------------------------------
def generate_recommendation(data: SurveySchema, db: Session, top_n: int = 5):
    """Compute user's recommended graduate major and top N job matches."""

    profile = _estimate_user_profile(data)
    jobs = db.query(Job).all()
    if not jobs:
        return {
            "recommended_major": "MS in Information Systems",
            "top_jobs": [],
        }

    # Load skills and knowledge aggregates
    skill_aggs = get_skill_aggregates(db)

    # Score each job
    scored = []
    for job in jobs:
        s = _score_job_for_user(job, profile, skill_aggs)
        scored.append((s, job))

    # Deduplicate by SOC code
    unique = {}
    for s, j in scored:
        if j.soc_code not in unique:
            unique[j.soc_code] = (s, j)

    scored = list(unique.values())
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:top_n]

    major = _map_focus_to_major(profile["focus_pref"])

    top_jobs = [
        {
            "title": j.title,
            "soc_code": j.soc_code,
            "score": round(float(s), 3),
            "focus_area": j.focus_area,
            "description": j.description,
            "job_zone": j.job_zone,
        }
        for s, j in top
    ]

    return {
        "recommended_major": major,
        "top_jobs": top_jobs,
    }
