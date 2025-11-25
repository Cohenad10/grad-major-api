import csv
import psycopg2
from pathlib import Path

DB_NAME = "SurveyData"
DB_USER = "postgres"
DB_PASSWORD = "Mustang"
DB_HOST = "localhost"
DB_PORT = "5432"

ONET_DIR = Path("data/onet")
TASKS_DWAS_FILE = ONET_DIR / "Tasks to DWAs.txt"
DWA_REF_FILE = ONET_DIR / "DWA Reference.txt"


def connect_db():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )


def load_dwas():
    """
    Approximate pipeline:

    - DWA Reference.txt: maps DWA IDs -> DWA Title
    - Tasks to DWAs.txt: links tasks -> DWA IDs (and sometimes SOC codes)
      In some versions, Tasks to DWAs.txt already has 'O*NET-SOC Code'.
    """

    if not TASKS_DWAS_FILE.exists():
        raise FileNotFoundError(f"Missing {TASKS_DWAS_FILE}")
    if not DWA_REF_FILE.exists():
        raise FileNotFoundError(f"Missing {DWA_REF_FILE}")

    # 1) Load DWA ID -> Title from DWA Reference
    dwa_title_map = {}
    with DWA_REF_FILE.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        # Common headers: 'DWA ID', 'DWA Title'
        for row in reader:
            dwa_id = row["DWA ID"].strip()
            dwa_title = row["DWA Title"].strip()
            dwa_title_map[dwa_id] = dwa_title

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM job_activities;")

    count = 0

    with TASKS_DWAS_FILE.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        # You may need to adjust these fieldnames based on file header.
        # Look for something like:
        # 'O*NET-SOC Code', 'DWA ID', 'Task ID', 'Data Value' (importance)
        for row in reader:
            soc = row.get("O*NET-SOC Code", "").strip()
            dwa_id = row["DWA ID"].strip()
            dwa_title = dwa_title_map.get(dwa_id, "").strip()
            importance_str = row.get("Data Value") or row.get("DWA Importance") or ""
            importance = float(importance_str) if importance_str else None

            if not soc or not dwa_id or not dwa_title:
                continue

            cur.execute(
                """
                INSERT INTO job_activities (soc_code, dwa_id, dwa_title, importance)
                VALUES (%s, %s, %s, %s)
                """,
                (soc, dwa_id, dwa_title, importance),
            )
            count += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"Inserted {count} rows into job_activities")


if __name__ == "__main__":
    load_dwas()
