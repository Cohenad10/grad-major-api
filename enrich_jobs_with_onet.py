import csv
import psycopg2
from pathlib import Path

DB_NAME = "SurveyData"
DB_USER = "postgres"
DB_PASSWORD = "Mustang"
DB_HOST = "localhost"
DB_PORT = "5432"

ONET_DIR = Path("data/onet")
JOB_ZONES_FILE = ONET_DIR / "Job Zones.txt"
INTERESTS_FILE = ONET_DIR / "Interests.txt"


def connect_db():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )


def load_job_zones():
    if not JOB_ZONES_FILE.exists():
        print(f"Missing {JOB_ZONES_FILE}")
        return

    conn = connect_db()
    cur = conn.cursor()

    updated = 0

    # Job Zones.txt: O*NET-SOC Code, Job Zone, Date, Domain Source
    with JOB_ZONES_FILE.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            soc = row["O*NET-SOC Code"].strip()
            zone = int(row["Job Zone"])
            cur.execute(
                "UPDATE jobs SET job_zone = %s WHERE soc_code = %s",
                (zone, soc),
            )
            if cur.rowcount > 0:
                updated += cur.rowcount

    conn.commit()
    cur.close()
    conn.close()
    print(f"Updated job_zone for {updated} jobs")


def load_interests():
    if not INTERESTS_FILE.exists():
        print(f"Missing {INTERESTS_FILE}")
        return

    riasec_map = {}

    # Interests.txt: O*NET-SOC Code, Element Name, Scale ID, Data Value, ...
    with INTERESTS_FILE.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            soc = row["O*NET-SOC Code"].strip()
            element = row["Element Name"].strip().lower()
            val = float(row["Data Value"])

            if "realistic" in element:
                key = "R"
            elif "investigative" in element:
                key = "I"
            elif "artistic" in element:
                key = "A"
            elif "social" in element:
                key = "S"
            elif "enterprising" in element:
                key = "E"
            elif "conventional" in element:
                key = "C"
            else:
                continue

            if soc not in riasec_map:
                riasec_map[soc] = {}
            riasec_map[soc][key] = val

    conn = connect_db()
    cur = conn.cursor()
    updated = 0

    for soc, scores in riasec_map.items():
        r = scores.get("R")
        i = scores.get("I")
        a = scores.get("A")
        s = scores.get("S")
        e = scores.get("E")
        c = scores.get("C")

        cur.execute(
            """
            UPDATE jobs
            SET riasec_r = %s,
                riasec_i = %s,
                riasec_a = %s,
                riasec_s = %s,
                riasec_e = %s,
                riasec_c = %s
            WHERE soc_code = %s
            """,
            (r, i, a, s, e, c, soc),
        )
        if cur.rowcount > 0:
            updated += cur.rowcount

    conn.commit()
    cur.close()
    conn.close()
    print(f"Updated RIASEC scores for {updated} jobs")


if __name__ == "__main__":
    load_job_zones()
    load_interests()
