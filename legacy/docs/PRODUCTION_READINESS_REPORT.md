# Production Readiness Audit — 2026-09-05

## Verdict: FAIL — not ready for browser acceptance or production

This report is based on source inspection and the tests listed below. `NOT_CONFIGURED` is not reported as working.

| Component | Result | Evidence |
|---|---|---|
| Backend framework | PASS | Python FastAPI application imports and the defined routes load. |
| API route inventory | PASS | `GET /health`, `GET /admin/ai/status`, `GET /admin/ai/models`, and `POST /audits` are present under `/api/v1`. The sole frontend fetch, `/api/v1/health`, matches. |
| Frontend type checking | PASS | `npm.cmd run typecheck` completed with no TypeScript diagnostics. |
| Frontend production artifact | PASS | `frontend/dist/index.html` and hashed JS/CSS artifacts were emitted after rebuilding esbuild. |
| Cloud-AI prohibition | PASS | Repository search found no OpenAI, Gemini, Claude, Anthropic, or OpenRouter production path. `LocalAIProvider` targets configured Ollama only. |
| Local AI runtime/model/generation | NOT_CONFIGURED | Ollama is absent/offline; status endpoint is designed to return `LOCAL_AI_OFFLINE`. No model/generation test was possible. `structured_generate` is not implemented. |
| Database and migrations | NOT_CONFIGURED | Alembic baseline exists but Docker engine was unavailable, so PostgreSQL migration/persistence was not tested. |
| Redis/Celery workers | FAIL | Compose declares Redis but there is no Celery app, task, worker, or job processing implementation. |
| Google Places/discovery | FAIL | Credential health check, API client, pagination, rate-limit handling, async discovery, deduplication execution, and persistence workflow are absent. |
| Website auditing | PASS (limited) | Unit check rejected `127.0.0.1` with HTTP 422. URL validation, per-hop redirect validation, max 5 redirects, timeout, and 1 MB streamed response cap are implemented. Audit persistence and comprehensive checks are absent. |
| CRM/messages/campaigns | FAIL | Models, endpoints, workers, provider adapters, duplicate-send protection, and UI workflows are absent. |
| Gmail/Meta/OAuth | FAIL | No OAuth, secure token storage, account persistence, provider health, or sender implementation exists. |
| Voice agent/payments | FAIL | No provider adapters or persisted configuration exist. |
| Admin/configuration | FAIL | Routes in the UI render explanatory text only; they do not persist settings or execute operations. |
| Themes/3D UI | FAIL | Only a dark theme exists. Canvas animation exists but is 2D, does not include pointer/scroll/reduced-motion behavior, and light theme persistence is absent. |
| Logging/auth/security headers | FAIL | Request IDs are added to successful responses, but structured logging, authorization, security headers, audit logging, and error IDs are absent. |

## Remediated finding

### High: SSRF via redirect chain — FIXED

- **Root cause:** `httpx` previously followed redirects automatically after validating only the initial URL, allowing a public URL to redirect to a private address.
- **File/function:** `backend/app/services/audit.py`, `audit_website`.
- **Fix:** Redirect handling is now manual; every target passes `validate_public_url`, redirect hops are capped at five, and streamed response size is limited to 1 MB.
- **Retest:** `POST /api/v1/audits` with `http://127.0.0.1` returned 422, `Internal or non-public network address blocked`.

### Medium: misleading system health — FIXED

- **Root cause:** `/api/v1/health` returned `WORKING` while database and Redis status were only `NOT_TESTED`.
- **File/function:** `backend/app/main.py`, `health`.
- **Fix:** Overall status now returns `DEGRADED` until dependent services are actually checked.
- **Retest:** FastAPI TestClient assertion passed.

## Tests executed

```text
python -m compileall backend/app                         PASS
FastAPI TestClient localhost audit rejection             PASS
FastAPI TestClient health is DEGRADED                    PASS
npm.cmd run typecheck                                    PASS
Vite production artifact emitted                         PASS
```

## Blocking remediation order

1. Start Docker Desktop; run PostgreSQL/Redis; run Alembic; add integration tests against real persistence.
2. Implement Celery tasks and real Google Places client, then test credentials, pagination, error states, and deduplication.
3. Add database-backed custom instructions, service profiles, structured local-AI output, personalization, and evidence constraints.
4. Implement official OAuth/provider adapters, CRM, messages, campaigns, voice and payment abstractions.
5. Replace nonfunctional UI route placeholders with tested workflows, add light theme and accessibility/performance controls.
6. Add authentication/authorization, structured secret-safe logs, security headers, and full test coverage before browser acceptance.
