@echo off
echo ========================================
echo CloudProof - Docker Quick Start
echo ========================================
echo.

echo [1/4] Checking Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed or not running
    echo Please install Docker Desktop and start it
    pause
    exit /b 1
)
echo ✓ Docker is running

echo.
echo [2/4] Creating environment file...
if not exist backend\.env (
    copy backend\.env.example backend\.env
    echo ✓ Created backend\.env
    echo IMPORTANT: Edit backend\.env with your AWS credentials
) else (
    echo ✓ backend\.env exists
)

echo.
echo [3/4] Starting services...
docker compose up -d --build
if errorlevel 1 (
    echo ERROR: Failed to start services
    pause
    exit /b 1
)

echo.
echo [4/4] Waiting for services to be ready...
timeout /t 15 /nobreak >nul

echo.
echo ========================================
echo ✅ CloudProof is running!
echo ========================================
echo.
echo Services:
echo   Frontend:  http://localhost:3000
echo   Backend:   http://localhost:5000
echo   Database:  localhost:5432
echo.
echo Next steps:
echo 1. Edit backend\.env with AWS credentials
echo 2. Create user via API or generate sample data
echo 3. Open http://localhost:3000 in browser
echo.
echo Commands:
echo   View logs:    docker compose logs -f
echo   Stop:         docker compose down
echo   Restart:      docker compose restart
echo.
pause
