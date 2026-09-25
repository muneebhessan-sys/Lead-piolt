# API Route Audit

Current FastAPI route inventory:

| Method | Route | Status |
|---|---|---|
| GET | `/api/v1/health` | Implemented; service state is degraded until dependencies are verified. |
| GET | `/api/v1/admin/ai/status` | Implemented; performs local Ollama reachability check. |
| GET | `/api/v1/admin/ai/models` | Implemented; returns 503 if local Ollama is unavailable. |
| POST | `/api/v1/audits` | Implemented; validates and audits public HTTP(S) URLs. |

The frontend makes one API request, `/api/v1/health`, which has a matching route. The UI does not yet issue requests for lead discovery, administration, CRM, messages, calls, payments, or campaigns because their required backends are not implemented. Those workflows must not be displayed as available.

## Phase 2 additions

The backend now also provides Google integration state/test, real discovery (when configured), lead listing, persisted service-profile configuration, per-business audit persistence, evidence-bound message draft/approval, and persistent jobs. The frontend is not yet wired to those additional endpoints, so there are no new frontend/backend request mismatches.
