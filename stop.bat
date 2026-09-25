@echo off
setlocal EnableExtensions
color 0C
title LeadPilot Stopper

echo [INFO] Stopping LeadPilot...

for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":8000 " ^| findstr LISTENING 2^>nul') do (
  echo [INFO] Stopping backend PID %%P
  taskkill /F /PID %%P >nul 2>&1
)

for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":5173 " ^| findstr LISTENING 2^>nul') do (
  echo [INFO] Stopping frontend PID %%P
  taskkill /F /PID %%P >nul 2>&1
)

for /f "skip=1 tokens=2" %%P in ('tasklist /v /fo csv /nh ^| findstr /i "LeadPilot Backend" 2^>nul') do (
  taskkill /F /PID %%P >nul 2>&1
)

for /f "skip=1 tokens=2" %%P in ('tasklist /v /fo csv /nh ^| findstr /i "LeadPilot Frontend" 2^>nul') do (
  taskkill /F /PID %%P >nul 2>&1
)

echo.
echo LeadPilot stopped.
echo.
pause >nul
exit /b 0
