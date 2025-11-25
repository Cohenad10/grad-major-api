# Graduate Major & Job Recommendation System

This project provides a recommendation system that matches students with suitable graduate majors and top job roles based on survey responses and occupational data from the U.S. O*NET database.

The application uses FastAPI for the backend, PostgreSQL for data storage, and a custom scoring engine that compares user survey profiles to O*NET job attributes such as skills, knowledge areas, interests, job zones, and job descriptions.

---

## Features

- Web-based survey for collecting user interests, preferences, and skill ratings  
- FastAPI backend with JSON endpoints  
- PostgreSQL database storing jobs, survey responses, skills, and knowledge data  
- ETL scripts for importing O*NET datasets  
- Job recommendation engine returning ranked occupations  
- Graduate major suggestions based on user preferences and job characteristics  
- Admin dashboard for reviewing submissions and job counts  

---

## Project Structure

grad-major-api/
├── main.py
├── recommendation.py
├── models.py
├── schemas.py
├── database.py
│
├── routes/
│ └── survey.py
│
├── static/
│ └── survey.html
│
├── templates/
│ └── admin.html
│
├── data/onet/
│ └── (O*NET .txt files)
│
├── load_jobs_from_onet.py
├── enrich_jobs_with_onet.py
├── load_skills_knowledge.py
└── load_dwas.py

---

## Setup

### Install dependencies

pip install -r requirements.txt

### Run the ETL loaders

python load_jobs_from_onet.py
python enrich_jobs_with_onet.py
python load_skills_knowledge.py
python load_dwas.py # optional


### Start the server


Survey UI: http://127.0.0.1:8000/


Admin dashboard: http://127.0.0.1:8000/admin


---

## Recommendation Logic

The engine evaluates each occupation using:

- Survey-derived user profile  
- O*NET Skills (importance/level)  
- O*NET Knowledge areas  
- RIASEC interest alignment  
- Job Zone (education requirement)  
- Job role category (data analysis, cybersecurity, systems management, etc.)

Jobs are scored, ranked, and returned with major recommendations.

---

## Data Sources

This project uses publicly available O*NET content model datasets, including:

- Occupation Data  
- Skills  
- Knowledge  
- Interests (RIASEC)  
- Job Zones  
- DWAs (optional)

Place all files in:  

data/onet/

---

## License

For academic and research use only.

