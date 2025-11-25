import csv
import psycopg2
from pathlib import Path

# ---------- DB CONFIG ----------
DB_NAME = "SurveyData"
DB_USER = "postgres"
DB_PASSWORD = "Mustang"
DB_HOST = "localhost"
DB_PORT = "5432"

# ---------- FILE PATH ----------
ONET_DIR = Path("data/onet")
OCCUPATION_DATA_FILE = ONET_DIR / "Occupation Data.txt"


def connect_db():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )


def is_msis_related(title: str, soc_code: str) -> bool:
    """
    Basic filter: keep occupations that are clearly IT / IS / data / cyber.
    Tune this list as needed.
    """
    t = title.lower()
    if any(
        kw in t
        for kw in [
            "information systems",
            "information security",
            "cyber",
            "database",
            "network",
            "computer systems",
            "data scientist",
            "data analyst",
            "software",
            "cloud",
            "it ",
            "technology manager",
        ]
    ):
        return True

    # IT-related SOC groups
    if soc_code.startswith("15-12") or soc_code.startswith("15-121") or soc_code.startswith("15-124"):
        return True
    if soc_code.startswith("11-3021"):  # Computer and Information Systems Managers
        return True

    return False


def rough_scores_from_title(title: str):
    """
    Very rough heuristic scores based on keywords in job title.
    These fill your required_* and preference columns.
    """
    t = title.lower()
    data_skill = 3
    tech_interest = 3
    comm = 3
    stability = 4
    salary = 4
    remote = True

    if "analyst" in t or "data" in t:
        data_skill = 5
        tech_interest = max(tech_interest, 4)

    if any(kw in t for kw in ["security", "cyber"]):
        tech_interest = 5
        stability = max(stability, 4)

    if any(kw in t for kw in ["manager", "director", "lead", "project"]):
        comm = 4
        salary = 5

    if "cloud" in t:
        tech_interest = 5

    return data_skill, tech_interest, comm, stability, salary, remote


def map_focus_area(title: str):
    """
    Map jobs into your survey's role categories:
    - systems management
    - data analysis
    - technology design
    - cybersecurity
    """
    t = title.lower()
    if any(kw in t for kw in ["security", "cyber"]):
        return "cybersecurity"
    if any(kw in t for kw in ["data", "analytics", "business intelligence"]):
        return "data analysis"
    if any(kw in t for kw in ["architect", "engineer", "developer", "designer"]):
        return "technology design"
    return "systems management"


def load_jobs():
    if not OCCUPATION_DATA_FILE.exists():
        raise FileNotFoundError(f"Could not find {OCCUPATION_DATA_FILE}")

    conn = connect_db()
    cur = conn.cursor()

    inserted = 0

    # Occupation Data.txt: tab-delimited with columns like:
    # O*NET-SOC Code, Title, Description, ...
    with OCCUPATION_DATA_FILE.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            soc_code = row["O*NET-SOC Code"].strip()
            title = row["Title"].strip()
            description = row.get("Description", "").strip()

            if not is_msis_related(title, soc_code):
                continue

            focus_area = map_focus_area(title)
            data_skill, tech_interest, comm, stability, salary, remote = rough_scores_from_title(
                title
            )

            cur.execute(
                """
                INSERT INTO jobs (
                    soc_code,
                    title,
                    description,
                    focus_area,
                    required_data_skill,
                    required_tech_interest,
                    required_communication,
                    stability_level,
                    salary_level,
                    remote_possible
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    soc_code,
                    title,
                    description,
                    focus_area,
                    data_skill,
                    tech_interest,
                    comm,
                    stability,
                    salary,
                    remote,
                ),
            )
            inserted += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"Inserted {inserted} MSIS-related jobs into jobs table.")


if __name__ == "__main__":
    load_jobs()
