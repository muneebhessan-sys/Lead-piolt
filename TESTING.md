# Testing

From `backend`, run `alembic upgrade head`, `python -m compileall app`, then API tests. From `frontend`, run `npm.cmd run typecheck` and `npm.cmd run build`. No Docker, PostgreSQL, Redis, Celery, or Ollama is required.
