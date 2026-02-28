@echo off
setlocal

cd /d "%~dp0"

echo [1/5] Checking Python...
set "PY_EXE="

where py >NUL 2>NUL
if not errorlevel 1 (
    py -3 -c "import sys" >NUL 2>NUL
    if not errorlevel 1 set "PY_EXE=py -3"
)

if "%PY_EXE%"=="" (
    where python >NUL 2>NUL
    if not errorlevel 1 (
        python -c "import sys" >NUL 2>NUL
        if not errorlevel 1 set "PY_EXE=python"
    )
)

if "%PY_EXE%"=="" (
    echo Python 3.10+ not found.
    echo Please install Python first: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [2/5] Creating virtual environment...
if not exist ".venv\Scripts\python.exe" (
    %PY_EXE% -m venv ".venv"
    if errorlevel 1 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
)

echo [3/5] Installing dependencies...
".venv\Scripts\python.exe" -m pip install -U pip
if errorlevel 1 (
    echo Failed to upgrade pip.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install requirements.
    pause
    exit /b 1
)

echo [4/5] Opening browser...
start "" "http://127.0.0.1:5000"

echo [5/5] Starting app... (close this window to stop)
".venv\Scripts\python.exe" app.py

echo App stopped.
pause
