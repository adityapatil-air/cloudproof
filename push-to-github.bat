@echo off
echo ========================================
echo CloudProof - Git Push Helper
echo ========================================
echo.

echo This script will help you push to GitHub
echo.

set /p REPO_URL="Enter your GitHub repository URL: "

if "%REPO_URL%"=="" (
    echo ERROR: Repository URL is required
    pause
    exit /b 1
)

echo.
echo [1/5] Initializing Git repository...
git init
if errorlevel 1 (
    echo Git already initialized or error occurred
)

echo.
echo [2/5] Adding all files...
git add .

echo.
echo [3/5] Creating commit...
git commit -m "Initial commit: CloudProof - AWS Activity Tracker"

echo.
echo [4/5] Setting main branch...
git branch -M main

echo.
echo [5/5] Adding remote and pushing...
git remote add origin %REPO_URL%
git push -u origin main

echo.
echo ========================================
echo ✅ Code pushed to GitHub!
echo ========================================
echo.
echo Repository: %REPO_URL%
echo.
pause
