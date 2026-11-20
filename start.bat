@echo off
title Financial AI - System Launcher
color 0A

echo ====================================================================
echo    AI-Powered Personal Financial Decision Support System
echo ====================================================================
echo.
echo [1/3] Starting Backend Server (FastAPI on Port 8000)...
cd /d "%~dp0backend"
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found in backend\.venv
    echo Please ensure python virtual environment is setup.
    pause
    exit /b 1
)

start "Financial AI - Backend API (Port 8000)" cmd /k "cd /d ""%~dp0backend"" && title Financial AI - Backend (Port 8000) && color 0B && echo Starting FastAPI Backend on http://localhost:8000 ... && .venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/3] Starting Frontend Dashboard (Next.js on Port 3000)...
cd /d "%~dp0frontend"
if not exist "node_modules" (
    echo [ERROR] node_modules not found in frontend directory.
    echo Please run 'npm install' in frontend folder.
    pause
    exit /b 1
)

start "Financial AI - Frontend UI (Port 3000)" cmd /k "cd /d ""%~dp0frontend"" && title Financial AI - Frontend (Port 3000) && color 0D && echo Starting Next.js Frontend on http://localhost:3000 ... && npm start"

echo.
echo [3/3] Waiting for servers to initialize...
timeout /t 4 /nobreak >nul

echo Opening browser at http://localhost:3000 ...
start http://localhost:3000

echo.
echo ====================================================================
echo    SUCCESS: All services are now running!
echo    - Frontend Dashboard: http://localhost:3000
echo    - Backend API Docs:   http://localhost:8000/docs
echo.
echo    To stop all services anytime, simply run 'stop.bat'.
echo ====================================================================
echo.
pause
