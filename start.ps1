$ErrorActionPreference = 'Stop'

$root = $PSScriptRoot
$backendDir = Join-Path $root 'backend'
$frontendDir = Join-Path $root 'frontend'
$backendUrl = 'http://127.0.0.1:8000'
$backendHealthUrl = 'http://127.0.0.1:8000/healthz'
$frontendUrl = 'http://127.0.0.1:5173'
$adminUrl = 'http://127.0.0.1:5173/admin'

function Wait-ForUrl($url, $timeoutSeconds = 30) {
  $deadline = (Get-Date).AddSeconds($timeoutSeconds)
  while ((Get-Date) -lt $deadline) {
    try {
      Invoke-WebRequest -UseBasicParsing $url -TimeoutSec 3 -ErrorAction Stop | Out-Null
      return $true
    } catch {
      Start-Sleep -Seconds 1
    }
  }
  return $false
}

function Kill-Port($port) {
  $matches = netstat -ano | Select-String ":$port\s+.*LISTENING" 
  foreach ($line in $matches) {
    $parts = $line.ToString() -split '\s+'
    $pid = $parts[-1]
    if ($pid -match '^\d+$') {
      Write-Host "[INFO] Killing process $pid on port $port" -ForegroundColor Yellow
      Stop-Process -Id ([int]$pid) -Force -ErrorAction SilentlyContinue
    }
  }
}

Write-Host '===============================================' -ForegroundColor Green
Write-Host '  LeadPilot Launcher (PowerShell)' -ForegroundColor Green
Write-Host '===============================================' -ForegroundColor Green

try {
  $pythonCmd = $null
  try {
    python --version | Out-Null
    $pythonCmd = 'python'
  } catch {
    try {
      py --version | Out-Null
      $pythonCmd = 'py'
    } catch {
      throw 'Python 3.11+ is required. Install it from https://www.python.org/downloads/windows/'
    }
  }

  if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    throw 'Node.js is required. Install it from https://nodejs.org/en/download/'
  }
  if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw 'npm is required. Install Node.js 18+ from https://nodejs.org/en/download/'
  }

  $venvPython = Join-Path $backendDir '.venv\Scripts\python.exe'
  if (-not (Test-Path $venvPython)) {
    Write-Host '[INFO] Creating backend virtual environment...' -ForegroundColor Yellow
    Push-Location $backendDir
    & $pythonCmd -m venv .venv
    Pop-Location
    if ($LASTEXITCODE -ne 0) { throw 'Failed to create the backend virtual environment.' }
  }

  $venvPython = Join-Path $backendDir '.venv\Scripts\python.exe'
  & $venvPython -c "import uvicorn" 2>$null
  if ($LASTEXITCODE -ne 0) {
    Write-Host '[INFO] Installing backend dependencies...' -ForegroundColor Yellow
    Push-Location $backendDir
    & $venvPython -m pip install -r requirements.txt
    Pop-Location
    if ($LASTEXITCODE -ne 0) { throw 'Backend dependency installation failed.' }
  }

  if (-not (Test-Path (Join-Path $frontendDir 'node_modules'))) {
    Write-Host '[INFO] Installing frontend dependencies...' -ForegroundColor Yellow
    Push-Location $frontendDir
    npm install
    Pop-Location
    if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' }
  }

  Kill-Port 8000
  Kill-Port 5173

  Write-Host '[1/3] Starting backend...' -ForegroundColor Cyan
  $backendArgs = @('-NoExit', '-Command', "Set-Location '$backendDir'; &'$venvPython' -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000")
  Start-Process powershell.exe @backendArgs

  if (-not (Wait-ForUrl $backendHealthUrl 30)) {
    throw 'Backend did not become ready within 30 seconds.'
  }

  Write-Host '[2/3] Starting frontend...' -ForegroundColor Cyan
  $frontendArgs = @('-NoExit', '-Command', "Set-Location '$frontendDir'; npm run dev -- --host 127.0.0.1 --port 5173")
  Start-Process powershell.exe @frontendArgs

  if (-not (Wait-ForUrl $frontendUrl 30)) {
    throw 'Frontend did not become ready within 30 seconds.'
  }

  Write-Host '[3/3] Opening browser...' -ForegroundColor Cyan
  Start-Process $frontendUrl

  Write-Host '===============================================' -ForegroundColor Green
  Write-Host '  LeadPilot is running' -ForegroundColor Green
  Write-Host "  Backend: $backendUrl" -ForegroundColor Green
  Write-Host "  Frontend: $frontendUrl" -ForegroundColor Green
  Write-Host "  Admin: $adminUrl" -ForegroundColor Green
  Write-Host '===============================================' -ForegroundColor Green
  Write-Host ''
  Read-Host 'Press Enter to close this launcher window'
}
catch {
  Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
  Read-Host 'Press Enter to exit'
  exit 1
}
