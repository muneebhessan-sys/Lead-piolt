# LeadPilot

LeadPilot is a local-first lead intelligence and outreach platform. The current runtime uses React/Vite for the interface, FastAPI for the backend, SQLite/Alembic for persistence, and deterministic Python services for scoring, message composition, and audit flows.

This implementation intentionally avoids fake AI or fake provider connectivity. It does not claim an unavailable service is connected and will only mark a provider as connected after a real verification call.

Features in this runtime:
- Lead discovery via official Google Places API when configured
- Business and lead tracking with lifecycle status updates
- Deterministic intelligence scoring and evidence-bound message drafting
- Local voice-agent status checks and call orchestration without fabricating success
- Persistent admin settings and encrypted secret storage
- Audit logging and structured JSON error responses

Quick start:
1. Copy `.env.example` to `.env`
2. From `backend`, install dependencies: `pip install -r requirements.txt`
3. Run migrations: `alembic upgrade head`
4. Start the API: `uvicorn app.main:app --reload`
5. From `frontend`, run `npm install` and `npm run dev`

Docker:
1. Build: `docker compose build`
2. Run: `docker compose up`
3. Backend UI: http://localhost:8000/docs
4. Frontend: http://localhost:5173

See [SETUP.md](SETUP.md) for the full local setup guide and [FINAL_SYSTEM_REPORT.md](FINAL_SYSTEM_REPORT.md) for architecture notes.
