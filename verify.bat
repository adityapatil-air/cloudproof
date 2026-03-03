@echo off
echo ========================================
echo CloudProof - Prerequisites Check
echo ========================================
echo.

set ERRORS=0

echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [X] Python not found
    set ERRORS=1
) else (
    python --version
    echo [OK] Python installed
)

echo.
echo Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo [X] Node.js not found
    set ERRORS=1
) else (
    node --version
    echo [OK] Node.js installed
)

echo.
echo Checking npm...
npm --version >nul 2>&1
if errorlevel 1 (
    echo [X] npm not found
    set ERRORS=1
) else (
    npm --version
    echo [OK] npm installed
)

echo.
echo Checking PostgreSQL...
psql --version >nul 2>&1
if errorlevel 1 (
    echo [X] PostgreSQL not found
    set ERRORS=1
) else (
    psql --version
    echo [OK] PostgreSQL installed
)

echo.
echo ========================================
if %ERRORS%==0 (
    echo All prerequisites met!
    echo Run: configure.bat
) else (
    echo Missing prerequisites. Install them first.
)
echo ========================================
echo.
pause
