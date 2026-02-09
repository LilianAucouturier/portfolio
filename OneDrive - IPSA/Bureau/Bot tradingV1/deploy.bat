@echo off
echo 🚀 Deployment script for Trading Bot
echo.

:: Check if git is installed
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Git is not installed or not in PATH.
    pause
    exit /b
)

:: Status
git status
echo.
set /p commit_msg="📝 Enter commit message (default: 'Update'): "
if "%commit_msg%"=="" set commit_msg=Update

:: Add, Commit, Push
echo.
echo ➕ Adding files...
git add .

echo 💾 Committing...
git commit -m "%commit_msg%"

echo ⬆️ Pushing to GitHub...
git push origin main

echo.
if %errorlevel% equ 0 (
    echo ✅ Deployment/Push successful!
) else (
    echo ❌ Error during push. Check your connection or credentials.
)
pause
