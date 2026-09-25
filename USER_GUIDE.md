# LeadPilot User Guide

## One-click launcher

Windows users can start the project with the desktop launcher:

1. Open the project root.
2. Double-click `start.bat`, or run `start.ps1` in PowerShell.
3. The launcher will start the backend and frontend in their own windows, wait for them to become ready, and open the browser automatically.
4. If you want to stop the active services, run `stop.bat`.

## Desktop shortcut

Run `create_shortcut.ps1` once to generate a shortcut on the Desktop named `LeadPilot`.

## Manual startup

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

### Access

- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- Admin: http://localhost:5173/admin

## Troubleshooting

- If the launcher closes immediately, check the generated logs in the backend/frontend console windows and run `stop.bat` before restarting.
- If Python is missing, install Python 3.11+.
- If Node.js is missing, install Node.js 18+.
- If ports 8000 or 5173 are already in use, run `stop.bat` before launching again.
- If the backend fails to start, inspect the backend console window for stack traces.
- If the frontend fails to start, inspect the frontend console window for npm/Vite errors.

## Notes

- The default theme is dark mode with a green accent and a Noor-inspired luxury layout.
- Use the floating theme toggle in the top-right corner to switch between light and dark modes.
- Keep the Python virtual environment and Node dependencies installed for local development.
