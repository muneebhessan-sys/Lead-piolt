# Architecture

React/Vite is presentation only. FastAPI owns validation and business logic. SQLite is the local system of record and Alembic is the schema migration tool. `LocalJobEngine` stores job state in SQLite with explicit pause/resume/cancel/retry transitions; it needs no broker. `IntelligenceEngine` is deterministic Python logic that only composes from supplied evidence. The audit service validates host resolution and rejects non-global IP addresses before requesting a URL.
