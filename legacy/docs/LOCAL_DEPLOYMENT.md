# Local Deployment

LeadPilot ka supported deployment Docker ke baghair 100% local hai.

## Required software

- Python 3.11 or newer
- Node.js 20 or newer
- npm

SQLite default database hai. PostgreSQL optional hai aur `DATABASE_URL` se
configure kiya ja sakta hai. Queue ke liye SQLite-backed `LocalJobEngine` use
hota hai; Redis aur Celery required nahi hain.

## Windows startup

Project root se:

```powershell
.\START_LEADPILOT.ps1
```

## Manual startup

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Frontend, doosre terminal me:

```powershell
cd frontend
npm install
npm run dev
```

URLs:

- API docs: http://localhost:8000/docs
- Frontend: http://localhost:5173

## Optional PostgreSQL

Local PostgreSQL install karke `.env` me `DATABASE_URL` set karein, phir:

```powershell
cd backend
alembic upgrade head
```

No Docker, Docker Compose, Redis, Celery, Ollama ya cloud AI required hai.