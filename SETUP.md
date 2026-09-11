# Setup

1. Copy `.env.example` to `.env`. The default SQLite database is a local file (`leadpilot_local.db`); no database server is needed.
2. From `backend`, run `pip install -r requirements.txt`, `alembic upgrade head`, then `uvicorn app.main:app --reload`.
3. From `frontend`, run `npm.cmd install`, then `npm.cmd run dev`.

On Windows, run `START_LEADPILOT.ps1` from the project folder to start the Alembic migration, FastAPI backend, Vite frontend, and browser together. A browser-installed PWA cannot start Python processes by itself; this launcher is the supported one-click local startup path.

Python 3.11+ and Node.js 20+ are sufficient. Docker, PostgreSQL, Redis, Celery, Ollama and LLaMA are not required. Google Places and Gmail/Meta credentials are optional server-side configuration for future official integrations. Voice-agent configuration is optional and is stored locally; it does not create or replace a voice agent.
