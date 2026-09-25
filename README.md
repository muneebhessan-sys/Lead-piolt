# LeadPilot

LeadPilot is a local-first lead intelligence and outreach platform. The current runtime uses React/Vite for the interface, FastAPI for the backend, SQLite/Alembic for persistence, and deterministic Python services for scoring, message composition, and audit flows.

The backend is configured for SQLite by default and is intentionally PostgreSQL-ready via `DATABASE_URL` and pool settings. It does not require PostgreSQL to run locally, but the same application can point to a hosted PostgreSQL service when the database driver and URL are configured.

This implementation intentionally avoids fake AI or fake provider connectivity. It does not claim an unavailable service is connected and will only mark a provider as connected after a real verification call.

Features in this runtime:
- Lead discovery via official Google Places API when configured
- Business and lead tracking with lifecycle status updates
- Deterministic intelligence scoring and evidence-bound message drafting
- Local voice-agent status checks and call orchestration without fabricating success
- Persistent admin settings and encrypted secret storage
- Audit logging and structured JSON error responses

## One-click launch

On Windows, use one of these from the project root:

1. Double-click `start.bat`
2. Run `start.ps1` in PowerShell
3. Run `python launcher.py`
4. Use the desktop shortcut created by `create_shortcut.ps1`

The launcher will:
- check Python and Node.js
- create or repair the backend virtual environment
- install missing Python and npm dependencies
- kill stale ports 8000 and 5173
- start backend and frontend in separate windows
- wait for both services to become available
- open the frontend in the browser
- leave the launcher window open until the user closes it

## Manual setup

1. Copy `.env.example` to `.env`
2. From `backend`, install dependencies: `pip install -r requirements.txt`
3. Run migrations: `alembic upgrade head`
4. Start the API: `uvicorn app.main:app --reload`
5. From `frontend`, run `npm install` and `npm run dev`

## Local deployment

1. Activate the Python virtual environment.
2. From `backend`, run `alembic upgrade head` and `uvicorn app.main:app --reload`.
3. From `frontend`, run `npm install` and `npm run dev`.
4. Backend UI: http://localhost:8000/docs
5. Frontend: http://localhost:5173

The supported deployment is 100% local: Python virtual environment, Uvicorn,
SQLite or an optional local PostgreSQL installation, and the SQLite-backed
`LocalJobEngine`. Node.js/npm are used for the frontend. Docker, Docker
Compose, Redis and Celery are not part of this project.

See [SETUP.md](SETUP.md) for the full local setup guide and [legacy/docs/FINAL_SYSTEM_REPORT.md](legacy/docs/FINAL_SYSTEM_REPORT.md) for historical architecture notes.
See [USER_GUIDE.md](USER_GUIDE.md) for launcher troubleshooting and [docs/LAUNCHER.md](docs/LAUNCHER.md) for the complete Windows launcher reference.
