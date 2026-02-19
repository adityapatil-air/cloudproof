@echo off
echo ========================================
echo CloudProof - Quick Start Script
echo ========================================
echo.

echo [1/5] Checking Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed or not running
    echo Please install Docker Desktop and try again
    pause
    exit /b 1
)
echo ✓ Docker is installed

echo.
echo [2/5] Creating environment file...
if not exist backend\.env (
    copy backend\.env.example backend\.env
    echo ✓ Created backend\.env - Please edit with your AWS credentials
) else (
    echo ✓ backend\.env already exists
)

echo.
echo [3/5] Starting services with Docker Compose...
docker-compose up -d
if errorlevel 1 (
    echo ERROR: Failed to start services
    pause
    exit /b 1
)
echo ✓ Services started

echo.
echo [4/5] Waiting for database to be ready...
timeout /t 10 /nobreak >nul
echo ✓ Database should be ready

echo.
echo [5/5] Initializing database schema...
docker-compose exec -T postgres psql -U postgres -d cloudproof < backend\schema.sql
if errorlevel 1 (
    echo WARNING: Database initialization may have failed
    echo You may need to run it manually
)

echo.
echo ========================================
echo ✅ CloudProof is ready!
echo ========================================
echo.
echo Services running at:
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:5000
echo   Database: localhost:5432
echo.
echo Next steps:
echo 1. Edit backend\.env with your AWS credentials
echo 2. Create a user: 
echo    curl -X POST http://localhost:5000/api/users -H "Content-Type: application/json" -d "{\"name\":\"Your Name\",\"email\":\"your@email.com\",\"role_arn\":\"your-role-arn\"}"
echo 3. Generate sample data:
echo    docker-compose exec backend python generate_sample_data.py
echo.
echo To stop: docker-compose down
echo To view logs: docker-compose logs -f
echo.
pause
