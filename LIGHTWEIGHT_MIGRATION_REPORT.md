# Lightweight Migration Report

## Preserved

- React/Vite/TypeScript frontend structure, routed dashboard, styling, and animated canvas background.
- Python/FastAPI backend and SSRF-protected website audit.
- Alembic migration workflow and original business/search-job tables.

## Changed

- Database: PostgreSQL connection target replaced with `sqlite:///./leadpilot_local.db`.
- AI: Ollama provider removed. `IntelligenceEngine` supplies deterministic scoring and evidence-bound message composition without any model or cloud service.
- Jobs: Redis/Celery dependencies replaced by `LocalJobEngine`, whose job records persist in SQLite and support enqueue, pause, resume, cancel, and retry state transitions.
- Administration: SQLite-persisted custom instruction profiles and configurable local voice-agent records were added.

## Removed from required runtime

- Docker/Compose, PostgreSQL, Redis, Celery, asyncpg, Ollama, and all cloud AI dependencies.

## Verification

- `alembic upgrade head`: PASS on SQLite.
- Python compilation: PASS.
- API smoke test: PASS for health endpoint, instruction persistence create/list, job enqueue/cancel transition, and private-IP SSRF rejection.
- Frontend TypeScript typecheck and production Vite build: PASS after the dashboard contract was migrated to the SQLite/local-intelligence health response.

## Remaining product scope

Google discovery, full worker execution handlers, CRM, message delivery, official OAuth providers, campaign processing, and a complete admin UI remain unimplemented. They are not represented as working.

## Start locally

```text
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

cd ../frontend
npm.cmd install
npm.cmd run dev
```
