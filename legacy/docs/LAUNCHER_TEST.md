# LeadPilot Launcher Test Plan

## Automated checks
1. Validate the Python launcher script compiles without syntax errors.
2. Start the project via `python launcher.py`.
3. Confirm the backend returns a healthy response on http://127.0.0.1:8000/healthz.
4. Confirm the frontend responds on http://127.0.0.1:5173.
5. Confirm the admin path resolves at http://127.0.0.1:5173/admin.
6. Stop both services and rerun the launcher to confirm the port cleanup works.

## Manual checks
- Run `start.bat` twice in a row.
- Run `start.ps1` from PowerShell.
- Run `create_shortcut.ps1` and confirm the desktop shortcut launches the project.
- Confirm the launcher does not disappear immediately if a prerequisite is missing.
- Confirm stale ports are re-used safely without a crash.

## Expected result
The project launches cleanly, both apps become reachable, the browser opens, and the launcher remains visible until the user closes it.
