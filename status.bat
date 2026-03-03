@echo off
echo ========================================
echo CloudProof - Status Check
echo ========================================
echo.

echo Checking Backend (Flask)...
curl -s http://localhost:5000/api/health >nul 2>&1
if errorlevel 1 (
    echo [X] Backend NOT running
    echo     Start with: cd backend ^&^& python app.py
) else (
    echo [OK] Backend running at http://localhost:5000
)

echo.
echo Checking Frontend (React)...
curl -s http://localhost:3000 >nul 2>&1
if errorlevel 1 (
    echo [X] Frontend NOT running
    echo     Start with: cd frontend ^&^& npm start
) else (
    echo [OK] Frontend running at http://localhost:3000
)

echo.
echo Checking Database...
psql -U postgres -d cloudproof -c "SELECT COUNT(*) FROM users;" >nul 2>&1
if errorlevel 1 (
    echo [X] Database issue
) else (
    echo [OK] Database connected
)

echo.
echo ========================================
pause
