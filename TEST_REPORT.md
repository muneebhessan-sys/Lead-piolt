# Test Report

- Python source compilation: PASS.
- Private-address SSRF rejection: PASS (`127.0.0.1` returns HTTP 422).
- Health endpoint truthfulness: PASS (returns `DEGRADED` without verified services).
- TypeScript typecheck: PASS.
- Vite build artifact generation: PASS.
- SQLite migration to revision `0002_lightweight_runtime`: PASS.
- SQLite instruction persistence and local-job cancel transition: PASS.
- PostgreSQL, Redis, Celery, Ollama and cloud AI are no longer required runtime dependencies.
- Google, OAuth, messaging, CRM, campaign, voice-agent calls and payments: NOT RUN — implementations/configuration remain unavailable.
