@echo off
echo ========================================
echo CloudProof - Prerequisites Check
echo ========================================
echo.

echo Checking installed software...
echo.

echo [1/3] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python NOT installed
    echo    Download: https://www.python.org/downloads/
    echo    Install Python 3.11 or higher
    set PYTHON_OK=0
) else (
    python --version
    echo ✅ Python installed
    set PYTHON_OK=1
)

echo.
echo [2/3] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js NOT installed
    echo    Download: https://nodejs.org/
    echo    Install Node.js 18 or higher
    set NODE_OK=0
) else (
    node --version
    echo ✅ Node.js installed
    set NODE_OK=1
)

echo.
echo [3/3] Checking PostgreSQL...
psql --version >nul 2>&1
if errorlevel 1 (
    echo ❌ PostgreSQL NOT installed
    echo    Download: https://www.postgresql.org/download/windows/
    echo    Install PostgreSQL 15 or higher
    set POSTGRES_OK=0
) else (
    psql --version
    echo ✅ PostgreSQL installed
    set POSTGRES_OK=1
)

echo.
echo ========================================
echo Summary
echo ========================================

if "%PYTHON_OK%"=="0" (
    echo.
    echo INSTALL PYTHON:
    echo 1. Go to: https://www.python.org/downloads/
    echo 2. Download Python 3.11 or higher
    echo 3. Run installer
    echo 4. CHECK "Add Python to PATH"
    echo 5. Click Install
    echo.
)

if "%NODE_OK%"=="0" (
    echo.
    echo INSTALL NODE.JS:
    echo 1. Go to: https://nodejs.org/
    echo 2. Download LTS version (18+)
    echo 3. Run installer
    echo 4. Click Next, Next, Install
    echo.
)

if "%POSTGRES_OK%"=="0" (
    echo.
    echo INSTALL POSTGRESQL:
    echo 1. Go to: https://www.postgresql.org/download/windows/
    echo 2. Download PostgreSQL 15 or higher
    echo 3. Run installer
    echo 4. Set password: postgres
    echo 5. Remember the password!
    echo.
)

if "%PYTHON_OK%"=="1" if "%NODE_OK%"=="1" if "%POSTGRES_OK%"=="1" (
    echo.
    echo ✅ All prerequisites installed!
    echo.
    echo Next step: Run setup-local.bat
    echo.
) else (
    echo.
    echo ⚠️ Please install missing software above
    echo    Then run this script again to verify
    echo.
)

pause
