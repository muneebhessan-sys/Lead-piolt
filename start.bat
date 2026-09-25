@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

color 0A
title LeadPilot Launcher

set "ROOT=%~dp0"
set "BACKEND_DIR=%ROOT%backend"
set "FRONTEND_DIR=%ROOT%frontend"
set "BACKEND_URL=http://127.0.0.1:8000"
set "BACKEND_HEALTH_URL=http://127.0.0.1:8000/healthz"
set "FRONTEND_URL=http://127.0.0.1:5173"
set "ADMIN_URL=http://127.0.0.1:5173/admin"

:banner
cls
echo.
echo ==============================================
echo   LeadPilot Launcher
echo ==============================================
echo.

:check_python
where python >nul 2>nul
if not errorlevel 1 (
  python --version >nul 2>nul || (
    echo [WARN] Python command is present but not usable. Trying py...
    py --version >nul 2>nul
    if errorlevel 1 (
      echo [ERROR] Python 3.11+ is required but not found.
      echo Please install Python from: https://www.python.org/downloads/windows/
      echo.
      pause >nul
      exit /b 1
    )
    set "PYTHON_CMD=py"
    goto check_node
  )
  set "PYTHON_CMD=python"
  goto check_node
)

py --version >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python 3.11+ is required but not found.
  echo Please install Python from: https://www.python.org/downloads/windows/
  echo.
  pause >nul
  exit /b 1
)
set "PYTHON_CMD=py"

:check_node
where node >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Node.js is required but not found.
  echo Please install Node.js 18+ from: https://nodejs.org/en/download/
  echo.
  pause >nul
  exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] npm is required but not found.
  echo Please install Node.js 18+ from: https://nodejs.org/en/download/
  echo.
  pause >nul
  exit /b 1
)

:check_backend_env
if not exist "%BACKEND_DIR%\.venv\Scripts\python.exe" (
  echo [INFO] Backend virtual environment not found. Creating it...
  cd /d "%BACKEND_DIR%"
  %PYTHON_CMD% -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Could not create backend virtual environment.
    echo Check Python installation and permissions.
    pause >nul
    exit /b 1
  )
)

:install_backend_deps
"%BACKEND_DIR%\.venv\Scripts\python.exe" -c "import uvicorn" >nul 2>nul
if errorlevel 1 (
  echo [INFO] Installing backend dependencies...
  cd /d "%BACKEND_DIR%"
  "%BACKEND_DIR%\.venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo [ERROR] Backend dependency installation failed.
    pause >nul
    exit /b 1
  )
)

:check_frontend_deps
if not exist "%FRONTEND_DIR%\node_modules" (
  echo [INFO] Frontend dependencies not found. Installing npm packages...
  cd /d "%FRONTEND_DIR%"
  npm install
  if errorlevel 1 (
    echo [ERROR] Frontend dependency installation failed.
    pause >nul
    exit /b 1
  )
)

:kill_port_conflicts
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":8000 " ^| findstr LISTENING 2^>nul') do (
  echo [INFO] Killing existing process on port 8000: %%P
  taskkill /F /PID %%P >nul 2>&1
)
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":5173 " ^| findstr LISTENING 2^>nul') do (
  echo [INFO] Killing existing process on port 5173: %%P
  taskkill /F /PID %%P >nul 2>&1
)

:launch_backend
echo [1/3] Starting backend...
start "LeadPilot Backend" /D "%BACKEND_DIR%" cmd /k "call .venv\Scripts\activate.bat && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

:wait_backend
echo [INFO] Waiting for backend to become ready...
for /L %%I in (1,1,30) do (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "try { (Invoke-WebRequest -UseBasicParsing '%BACKEND_HEALTH_URL%' -TimeoutSec 3 -ErrorAction Stop | Out-Null); exit 0 } catch { exit 1 }" >nul 2>&1
  if not errorlevel 1 goto backend_ready
  timeout /t 1 /nobreak >nul
)

echo [ERROR] Backend did not become ready within 30 seconds.
echo Check the LeadPilot Backend window for errors.
pause >nul
exit /b 1

:backend_ready
echo [INFO] Backend is ready.

:launch_frontend
echo [2/3] Starting frontend...
start "LeadPilot Frontend" /D "%FRONTEND_DIR%" cmd /k "npm run dev -- --host 127.0.0.1 --port 5173"

:wait_frontend
echo [INFO] Waiting for frontend to become ready...
for /L %%I in (1,1,30) do (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "try { (Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:5173' -TimeoutSec 3 -ErrorAction Stop | Out-Null); exit 0 } catch { exit 1 }" >nul 2>&1
  if not errorlevel 1 goto frontend_ready
  timeout /t 1 /nobreak >nul
)

echo [ERROR] Frontend did not become ready within 30 seconds.
echo Check the LeadPilot Frontend window for errors.
pause >nul
exit /b 1

:frontend_ready
echo [INFO] Frontend is ready.

:open_browser
echo [3/3] Opening browser...
timeout /t 2 /nobreak >nul
start "" http://localhost:5173

cls
echo.
echo ==============================================
echo   LeadPilot is running
echo ==============================================
echo   Backend: %BACKEND_URL%
echo   Frontend: %FRONTEND_URL%
echo   Admin: %ADMIN_URL%
echo ==============================================
echo.
echo   Press any key to close this launcher window.
echo   Backend and frontend remain running in their own windows.
echo ==============================================
echo.
pause >nul
exit /b 0
