@echo off
echo ========================================
echo CloudProof - Local Setup
echo ========================================
echo.

echo [1/3] Installing Python dependencies...
cd backend
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)
cd ..

echo.
echo [2/3] Installing Node dependencies...
cd frontend
call npm install
if errorlevel 1 (
    echo ERROR: Failed to install Node dependencies
    pause
    exit /b 1
)
cd ..

echo.
echo [3/3] Setup complete!
echo.
echo Next steps:
echo 1. Install PostgreSQL locally
echo 2. Create database: createdb cloudproof
echo 3. Run schema: psql -U postgres -d cloudproof -f backend\schema.sql
echo 4. Configure backend\.env with your AWS credentials
echo 5. Run: start-local.bat
echo.
pause
