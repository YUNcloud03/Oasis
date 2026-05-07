# OASIS Backend

FastAPI MVP backend for OASIS AI Smart Career Assistant & Growth Garden.

## Quick Start

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open API docs:

```text
http://127.0.0.1:8000/docs
```

## Environment

Default database is local SQLite:

```text
sqlite:///./oasis.db
```

For PostgreSQL:

```powershell
$env:DATABASE_URL="postgresql+psycopg://user:password@localhost:5432/oasis"
$env:JWT_SECRET_KEY="replace-with-a-long-random-secret"
```

## MVP Scope

Implemented in this scaffold:

- Auth register/login/me
- Profile read/update
- Educations CRUD
- Experiences CRUD
- Projects CRUD
- Skills CRUD
- Certificates CRUD
- Jobs CRUD and rule-based JD keyword extraction
- Applications and garden status state machine
- Garden overview
- Rule-based match score
- Multi-job comparison

AI resume generation is intentionally left as the next module so the core data and state logic is stable first.
