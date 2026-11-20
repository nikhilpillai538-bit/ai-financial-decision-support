@echo off
title Financial AI - Online Public Cloud Launcher
color 0B

echo ====================================================================
echo    AI-Powered Personal Financial Decision Support System
echo       [1-CLICK INSTANT ONLINE PUBLIC CLOUD DEPLOYMENT]
echo ====================================================================
echo.
echo [1/3] Starting FastAPI Backend on Port 8000...
cd /d "%~dp0backend"
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Python venv not found!
    pause
    exit /b 1
)
start "Financial AI - Backend API" cmd /k "cd /d ""%~dp0backend"" && title Backend API (Port 8000) && color 0B && .venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

echo [2/3] Starting Next.js Production Frontend on Port 3000...
cd /d "%~dp0frontend"
start "Financial AI - Frontend UI" cmd /k "cd /d ""%~dp0frontend"" && title Frontend UI (Port 3000) && color 0D && npm run start"

echo [3/3] Creating Secure Worldwide HTTPS Cloud Tunnel (Cloudflare)...
echo Please wait 5-10 seconds while the worldwide public URL is generated...
echo.

cd /d "%~dp0"
timeout /t 5 /nobreak >nul

start "Financial AI - Public Cloud URL" cmd /k "title Public Cloud URL && color 0A && echo ==================================================================== && echo   YOUR SECURE PUBLIC CLOUD URL IS GENERATING BELOW: && echo   Share the 'https://...trycloudflare.com' link with your professor! && echo ==================================================================== && echo. && npx --yes cloudflared tunnel --url http://localhost:3000"

echo ====================================================================
echo   SUCCESS: All services started!
echo   Check the green window for your public HTTPS link (trycloudflare.com).
echo   Anyone with this link can test the complete system live over the internet!
echo ====================================================================
echo.
pause
