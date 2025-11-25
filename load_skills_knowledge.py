import csv
import psycopg2
from pathlib import Path

DB_NAME = "SurveyData"
DB_USER = "postgres"
DB_PASSWORD = "Mustang"
DB_HOST = "localhost"
DB_PORT = "5432"

ONET_DIR = Path("data/onet")
SKILLS_FILE = ONET_DIR / "Skills.txt"
KNOWLEDGE_FILE = ONET_DIR / "Knowledge.txt"


def connect_db():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )


def load_skills():
    """
    Load Skills.txt into job_skills.
    O*NET Skills.txt usually has columns like:
      'O*NET-SOC Code', 'Element ID', 'Element Name', 'Scale ID', 'Data Value', ...
    Scale ID: 'IM' = Importance, 'LV' = Level.
    We'll collapse IM/LV into one row per (soc_code, element_id).
    """
    if not SKILLS_FILE.exists():
        raise FileNotFoundError(f"Missing {SKILLS_FILE}")

    # temp structure: (soc, element_id) -> {name, importance, level}
    skill_map = {}

    with SKILLS_FILE.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            soc = row["O*NET-SOC Code"].strip()
            element_id = row["Element ID"].strip()
            name = row["Element Name"].strip()
            scale_id = row["Scale ID"].strip()
            data_value = float(row["Data Value"])

            key = (soc, element_id)
            if key not in skill_map:
                skill_map[key] = {
                    "name": name,
                    "importance": None,
                    "level": None,
                }

            if scale_id == "IM":  # Importance
                skill_map[key]["importance"] = data_value
            elif scale_id == "LV":  # Level
                skill_map[key]["level"] = data_value

    conn = connect_db()
    cur = conn.cursor()

    # Clear old data if you like:
    cur.execute("DELETE FROM job_skills;")

    count = 0
    for (soc, element_id), vals in skill_map.items():
        cur.execute(
            """
            INSERT INTO job_skills (soc_code, element_id, skill_name, importance, level)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                soc,
                element_id,
                vals["name"],
                vals["importance"],
                vals["level"],
            ),
        )
        count += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"Inserted {count} rows into job_skills")


def load_knowledge():
    """
    Load Knowledge.txt into job_knowledge.
    Structure is similar to Skills.txt.
    """
    if not KNOWLEDGE_FILE.exists():
        raise FileNotFoundError(f"Missing {KNOWLEDGE_FILE}")

    know_map = {}

    with KNOWLEDGE_FILE.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            soc = row["O*NET-SOC Code"].strip()
            element_id = row["Element ID"].strip()
            name = row["Element Name"].strip()
            scale_id = row["Scale ID"].strip()
            data_value = float(row["Data Value"])

            key = (soc, element_id)
            if key not in know_map:
                know_map[key] = {
                    "name": name,
                    "importance": None,
                    "level": None,
                }

            if scale_id == "IM":
                know_map[key]["importance"] = data_value
            elif scale_id == "LV":
                know_map[key]["level"] = data_value

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM job_knowledge;")

    count = 0
    for (soc, element_id), vals in know_map.items():
        cur.execute(
            """
            INSERT INTO job_knowledge (soc_code, element_id, knowledge_name, importance, level)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                soc,
                element_id,
                vals["name"],
                vals["importance"],
                vals["level"],
            ),
        )
        count += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"Inserted {count} rows into job_knowledge")


if __name__ == "__main__":
    load_skills()
    load_knowledge()
