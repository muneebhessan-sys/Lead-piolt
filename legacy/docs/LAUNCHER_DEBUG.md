# LeadPilot Launcher Debug Report

## Summary
The original launcher stack was unreliable because it started services without validating prerequisites, readiness, or port conflicts. It also did not pause after launch, so the window could disappear before a user could inspect it.

## Root causes
- Missing Python and Node.js verification before launching.
- Missing `.venv` and `node_modules` bootstrap logic.
- Port 8000 and 5173 were never checked for stale listeners.
- Backend and frontend were started without waiting for their health checks.
- Browser open happened before the app was ready.
- Launcher windows did not remain open long enough for the user to notice errors.
- `stop.bat` lacked the same cleanup logic and could leave stale services running.

## Fixes applied
- Added prerequisite detection for Python 3.11+, Node.js, and npm.
- Auto-created the backend virtual environment when missing.
- Auto-installed missing backend and frontend dependencies.
- Killed stale listeners on 8000 and 5173.
- Waited for the backend `/healthz` route and the frontend root URL before declaring success.
- Opened the browser only after both services were online.
- Kept the launcher window open so the user can see startup status and exit gracefully.
- Added a PowerShell launcher and a hidden VBS launcher for silent desktop startup.

## Verified behavior
The runtime was checked with the app running locally and by testing the launcher flow against the app endpoints.
