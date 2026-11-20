@echo off
title Financial AI - Dev Mode Launcher
color 0E

echo ====================================================================
echo    AI-Powered Financial System (DEVELOPMENT MODE - HOT RELOAD)
echo ====================================================================
echo.
echo [1/3] Starting Backend Server (FastAPI with reload)...
start "Financial AI - Backend Dev (Port 8000)" cmd /k "cd /d ""%~dp0backend"" && title Backend Dev (8000) && color 0B && .venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/3] Starting Frontend Server (Next.js Dev with Hot Reload)...
start "Financial AI - Frontend Dev (Port 3000)" cmd /k "cd /d ""%~dp0frontend"" && title Frontend Dev (3000) && color 0D && npm run dev"

echo.
echo [3/3] Waiting for servers to initialize...
timeout /t 5 /nobreak >nul

echo Opening browser at http://localhost:3000 ...
start http://localhost:3000

echo.
echo ====================================================================
echo    DEV MODE RUNNING:
echo    - Frontend UI:        http://localhost:3000
echo    - Backend API Docs:   http://localhost:8000/docs
echo.
echo    Code changes will hot-reload automatically!
echo ====================================================================
echo.
pause
