# LeadPilot Windows Launcher

## Start

Double-click `start.bat` in the project root. It checks Python and Node.js, creates missing dependencies, clears stale ports, starts the backend and frontend, waits for readiness, waits two seconds, and opens `http://localhost:5173`.

PowerShell users can run `start.ps1`. The cross-platform Python launcher is `python launcher.py`. To create a desktop shortcut, run `create_shortcut.ps1` once.

## Stop

Run `stop.bat`. It stops listeners on ports 8000 and 5173 and pauses so the result remains visible.

## Troubleshooting

- Window flashes or closes: run `start.bat` from a Command Prompt so the error remains visible; the launcher pauses at every failure path.
- Python not found: install Python 3.11+ and ensure `python` or `py` is on PATH.
- Node not found: install Node.js 18+ and ensure `node` and `npm` are on PATH.
- Port already in use: run `stop.bat`, then run `start.bat` again.
- Backend does not become ready: inspect the LeadPilot Backend window and verify `http://127.0.0.1:8000/healthz`.
- Frontend does not become ready: inspect the LeadPilot Frontend window and verify `http://127.0.0.1:5173`.
- Browser does not open: visit `http://localhost:5173` manually after both service windows report ready.

The launchers intentionally do not fabricate provider connectivity. External integrations still require their real credentials and configuration.
