# API

- `GET /api/v1/health` — lightweight runtime state.
- `POST /api/v1/audits` — SSRF-protected public-website audit.
- `GET|POST /api/v1/admin/instructions` — persisted instruction profiles.
- `PUT|DELETE /api/v1/admin/instructions/{profile_id}` — profile modification.
- `GET|POST /api/v1/jobs` — persistent local job records.
- `POST /api/v1/jobs/{job_id}/{pause|resume|cancel|retry}` — job transition.
- `GET|PUT /api/v1/admin/voice-agent` — optional local-agent config.
- `POST /api/v1/intelligence/score` — deterministic score.
