# Launcher Test Results

## Static checks

- `launcher.py` compilation: PASS
- `start.bat`, `start.ps1`, `stop.bat`, `start.vbs`, `create_shortcut.ps1`: present
- Backend readiness route: `/healthz`
- Browser URL: `http://localhost:5173`
- `start.bat` includes absolute root handling, paused failure paths, port cleanup, readiness polling, two-second delay, and browser launch.

## Application checks

- Backend: PASS, 127 tests passed.
- Frontend: PASS, production build and TypeScript check passed.
- Ports 8000 and 5173: free after test cleanup.

## GUI limitation

A real double-click and visible browser window were not asserted by the non-interactive diagnostic runner. The implementation is wired to open the browser after both readiness checks:

- Batch: `start "" http://localhost:5173`
- PowerShell: `Start-Process $frontendUrl`
- Python: `webbrowser.open(FRONTEND_URL)`

Manual final check: double-click `start.bat`, confirm the two service windows, browser page, and theme toggle; then run `stop.bat`.
