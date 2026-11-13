@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating the project virtual environment...
    py -3 -m venv .venv
    if errorlevel 1 goto setup_failed
)

".venv\Scripts\python.exe" -c "import fastapi, uvicorn, requests, pydantic, dotenv, httpx, rapidfuzz, prometheus_client" >nul 2>&1
if errorlevel 1 (
    echo Installing project dependencies. This may take a few minutes the first time...
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto setup_failed
)

".venv\Scripts\python.exe" scripts\run_demo.py
if errorlevel 1 goto setup_failed
exit /b 0

:setup_failed
echo.
echo Demo could not start. Read the error above, then try run_demo.bat again.
pause
exit /b 1
