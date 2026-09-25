# Error Scan Raw Results

## Backend

- `python -m compileall app`: PASS
- `python -m pytest -q`: PASS, 127 passed, 1 deprecation warning
- `python -c "from app.main import app"`: PASS, `LeadPilot API`
- Database engine connection: PASS
- `python -m alembic current`: PASS, `0013_outbound_messaging (head)`
- `python -m alembic upgrade head`: PASS
- `python -m mypy app`: NOT RUN, mypy is not installed
- `python -m ruff check app`: NOT RUN, ruff is not installed

## Frontend

- Initial frontend build: FAILED because `node_modules` contained truncated package directories.
- `npm ci`: PASS, restored 208 packages with 0 vulnerabilities.
- Final `npm run build`: PASS
- Final `npm exec -- tsc --noEmit`: PASS
- ESLint: NOT RUN, ESLint is not installed or configured in `frontend/package.json`
- `npm audit --audit-level=high`: not used as a release gate because the package lock/toolchain was being repaired; dependency status remains a follow-up.

## Runtime and launcher

- Backend readiness route: `/healthz`
- Frontend readiness route: `/`
- Ports were free after diagnostic cleanup.
- `launcher.py` syntax: PASS
- Required launcher files: PASS
- Browser opening is implemented with `start`, `webbrowser.open`, and `Start-Process`; GUI browser display was not asserted by a headless command.

## Final runtime rerun

- Backend `/healthz`: HTTP 200
- Frontend `/`: HTTP 200
- Browser open request: issued successfully for `http://localhost:5173`

The initial scan also produced false failures when commands were run from the repository root. All application diagnostics above were rerun from their owning `backend` and `frontend` directories.
