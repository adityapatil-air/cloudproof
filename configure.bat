@echo off
echo ========================================
echo CloudProof - Complete Configuration
echo ========================================
echo.

echo [1/5] Installing Python dependencies...
cd backend
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)
cd ..

echo.
echo [2/5] Installing Node dependencies...
cd frontend
call npm install
if errorlevel 1 (
    echo ERROR: Failed to install Node dependencies
    pause
    exit /b 1
)
cd ..

echo.
echo [3/5] Setting up PostgreSQL database...
psql -U postgres -c "DROP DATABASE IF EXISTS cloudproof;"
psql -U postgres -c "CREATE DATABASE cloudproof;"
psql -U postgres -d cloudproof -f backend\schema.sql
if errorlevel 1 (
    echo WARNING: Database setup may have failed. Check PostgreSQL installation.
)

echo.
echo [4/5] Generating sample data...
cd backend
python generate_sample_data.py
cd ..

echo.
echo [5/5] Configuration complete!
echo.
echo ========================================
echo Ready to start!
echo ========================================
echo.
echo Run: start-local.bat
echo.
pause
