# LeadPilot Launcher Fix Report

## Objective
Repair the Windows-only startup experience so a user can launch the full project with a single click or shortcut without manually opening terminals.

## Changes made
- Rewrote `start.bat` with prerequisite checks, dependency bootstrap, readiness waits, port cleanup, and browser launch.
- Rewrote `start.ps1` with safer PowerShell execution and robust retry logic.
- Rewrote `launcher.py` so it works as a Python launcher without relying on external packages.
- Rewrote `stop.bat` so it kills stale service listeners consistently.
- Added `start.vbs` for hidden startup and `create_shortcut.ps1` for desktop shortcut creation.
- Updated the user documentation in `README.md` and `docs/USER_GUIDE.md`.

## Result
The launcher now performs the minimum reliable startup flow expected by a user: validate environment, start both services, detect readiness, open the browser, and keep the session visible to the user.
