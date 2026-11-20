@echo off
title Financial AI - Stop Services
color 0C

echo ====================================================================
echo    Stopping Financial AI System Services
echo ====================================================================
echo.

echo [1/2] Terminating processes on Port 8000 (Backend API)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo Killing PID %%a on port 8000 ...
    taskkill /f /pid %%a >nul 2>&1
)

echo [2/2] Terminating processes on Port 3000 (Frontend UI)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000" ^| findstr "LISTENING"') do (
    echo Killing PID %%a on port 3000 ...
    taskkill /f /pid %%a >nul 2>&1
)

echo.
echo ====================================================================
echo    All Financial AI services have been stopped successfully!
echo ====================================================================
echo.
timeout /t 3
