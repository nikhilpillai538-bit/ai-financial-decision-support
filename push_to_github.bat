@echo off
title Push Project to GitHub
color 0E

echo ====================================================================
echo      Deploy Project to Your GitHub Account
echo ====================================================================
echo.
echo Please create an empty repository on https://github.com/new
echo (Do NOT check 'Add README' or '.gitignore').
echo.
set /p REPO_URL="Paste your GitHub Repository URL here (e.g. https://github.com/username/repo.git): "

if "%REPO_URL%"=="" (
    echo [ERROR] No URL entered. Aborting.
    pause
    exit /b 1
)

cd /d "%~dp0"
echo.
echo [1/3] Setting git remote origin...
git remote remove origin 2>nul
git remote add origin %REPO_URL%

echo [2/3] Setting branch to main...
git branch -M main

echo [3/3] Pushing code to GitHub...
echo (If a browser window opens, please click 'Sign in with your browser')
echo.
git push -u origin main

if %ERRORLEVEL% equ 0 (
    echo.
    echo ====================================================================
    echo   SUCCESS: Project pushed to GitHub successfully!
    echo   Now you can connect this repo to Render and Vercel in 1 click!
    echo ====================================================================
) else (
    echo.
    echo [ERROR] Push failed. Please verify repository URL and your GitHub permissions.
)

echo.
pause
