# Cleanup Report

## Actions completed

- Moved historical root reports and setup notes to `legacy/docs/`.
- Moved the duplicate root `leadpilot_local.db` to `legacy/data/leadpilot_local.db`; the active database remains `backend/leadpilot_local.db`.
- Moved the unrelated empty root lockfile to `legacy/data/package-lock.root.json`; the active lockfile remains `frontend/package-lock.json`.
- Moved `docs/USER_GUIDE.md` to the required root `USER_GUIDE.md`.
- Removed generated `__pycache__`, `.pytest_cache`, `dist`, and TypeScript/Python cache artifacts after validation.
- Expanded `.gitignore` for secrets, databases, logs, caches, build output, temporary files, and editor artifacts.

## Preserved

- All backend source modules and migrations.
- All backend tests, including nested messaging tests.
- Frontend source, package manifest, and frontend lockfile.
- Active launchers and shortcut helpers.
- Required root docs: `README.md`, `ARCHITECTURE.md`, `SETUP.md`, `USER_GUIDE.md`.

No active source or test file was deleted. No duplicate module was moved because usage could not be safely disproved.
