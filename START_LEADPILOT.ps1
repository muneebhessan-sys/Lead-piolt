$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root 'backend'
$frontend = Join-Path $root 'frontend'

if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw 'Python 3.11+ is required.' }
if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) { throw 'Node.js 20+ is required.' }

Start-Process powershell.exe -ArgumentList @('-NoExit', '-ExecutionPolicy', 'Bypass', '-Command', "Set-Location '$backend'; `$env:PYTHONPATH='.'; alembic upgrade head; if (`$LASTEXITCODE -ne 0) { Write-Warning 'Database migration reported existing local schema drift; starting with the preserved database.' }; uvicorn app.main:app --host 127.0.0.1 --port 8000")
Start-Process powershell.exe -ArgumentList @('-NoExit', '-ExecutionPolicy', 'Bypass', '-Command', "Set-Location '$frontend'; npm.cmd run dev -- --host 127.0.0.1 --port 5173")

Write-Host 'LeadPilot services are starting.'
Write-Host 'Backend:  http://127.0.0.1:8000'
Write-Host 'Frontend: http://127.0.0.1:5173'
Start-Process 'http://127.0.0.1:5173'
