"""LeadPilot launcher: start backend + frontend + open browser."""
from __future__ import annotations

import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / 'backend'
FRONTEND = ROOT / 'frontend'
BACKEND_URL = 'http://127.0.0.1:8000/healthz'
FRONTEND_URL = 'http://127.0.0.1:5173'


def find_python() -> str | None:
    for candidate in (shutil.which('python'), shutil.which('py')):
        if candidate:
            return candidate
    return None


def ensure_python() -> str:
    python_bin = find_python()
    if not python_bin:
        raise RuntimeError('Python 3.11+ is required. Install it from https://www.python.org/downloads/windows/')
    return python_bin


def ensure_node() -> None:
    if shutil.which('node') is None or shutil.which('npm') is None:
        raise RuntimeError('Node.js and npm are required. Install them from https://nodejs.org/en/download/')


def port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return sock.connect_ex(('127.0.0.1', port)) == 0


def kill_port(port: int) -> None:
    if not port_in_use(port):
        return
    try:
        if sys.platform == 'win32':
            result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True, check=False)
            for line in result.stdout.splitlines():
                if f':{port} ' in line and 'LISTENING' in line:
                    parts = line.split()
                    pid = parts[-1]
                    if pid.isdigit():
                        subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True, check=False)
        else:
            subprocess.run(['fuser', '-k', f'{port}/tcp'], capture_output=True, check=False)
    except Exception:
        pass


def wait_for_url(url: str, timeout: int = 30) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as response:
                if response.status < 500:
                    return True
        except Exception:
            time.sleep(1)
    return False


def start_backend(python_cmd: str) -> subprocess.Popen:
    venv_python = BACKEND / '.venv' / ('Scripts' if sys.platform == 'win32' else 'bin') / ('python.exe' if sys.platform == 'win32' else 'python')
    if not venv_python.exists():
        print('[INFO] Creating backend venv...')
        subprocess.run([python_cmd, '-m', 'venv', str(BACKEND / '.venv')], check=True)
    if not (BACKEND / '.venv').exists():
        raise RuntimeError('Backend virtual environment was not created.')

    if sys.platform == 'win32':
        python_executable = venv_python
    else:
        python_executable = venv_python

    if not (BACKEND / '.venv').exists():
        raise RuntimeError('Backend venv missing.')

    try:
        subprocess.run([str(python_executable), '-c', 'import uvicorn'], cwd=str(BACKEND), check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print('[INFO] Installing backend dependencies...')
        subprocess.run([str(python_executable), '-m', 'pip', 'install', '-r', 'requirements.txt'], cwd=str(BACKEND), check=True)

    print('[1/3] Starting backend...')
    return subprocess.Popen(
        [str(python_executable), '-m', 'uvicorn', 'app.main:app', '--reload', '--host', '127.0.0.1', '--port', '8000'],
        cwd=str(BACKEND),
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0,
    )


def start_frontend() -> subprocess.Popen:
    if not (FRONTEND / 'node_modules').exists():
        print('[INFO] Installing frontend dependencies...')
        subprocess.run(['npm', 'install'], cwd=str(FRONTEND), check=True)

    print('[2/3] Starting frontend...')
    return subprocess.Popen(
        ['npm', 'run', 'dev', '--', '--host', '127.0.0.1', '--port', '5173'],
        cwd=str(FRONTEND),
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0,
        shell=False,
    )


def main() -> None:
    print('=' * 60)
    print(' LeadPilot Launcher')
    print('=' * 60)

    try:
        python_cmd = ensure_python()
        ensure_node()
        kill_port(8000)
        kill_port(5173)
        backend_proc = start_backend(python_cmd)
        if not wait_for_url(BACKEND_URL, timeout=30):
            raise RuntimeError('Backend did not become ready within 30 seconds.')
        frontend_proc = start_frontend()
        if not wait_for_url(FRONTEND_URL, timeout=30):
            raise RuntimeError('Frontend did not become ready within 30 seconds.')
        webbrowser.open(FRONTEND_URL)

        print('\n' + '=' * 60)
        print(' LeadPilot is running!')
        print(f' Backend:  http://127.0.0.1:8000')
        print(f' Frontend: {FRONTEND_URL}')
        print(' Admin:    http://127.0.0.1:5173/admin')
        print('=' * 60)
        print('\nPress Enter to close this launcher. The services keep running in their own windows.')
        try:
            input('')
        except KeyboardInterrupt:
            pass
    except Exception as exc:
        print(f'\n[ERROR] {exc}')
        try:
            input('\nPress Enter to exit...')
        except KeyboardInterrupt:
            pass
        sys.exit(1)


if __name__ == '__main__':
    main()
