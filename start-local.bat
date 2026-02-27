@echo off
echo ========================================
echo CloudProof - Starting Local Services
echo ========================================
echo.

echo Starting Backend (Flask)...
start "CloudProof Backend" cmd /k "cd backend && python app.py"

timeout /t 3 /nobreak >nul

echo Starting Frontend (React)...
start "CloudProof Frontend" cmd /k "cd frontend && npm start"

echo.
echo ========================================
echo Services starting...
echo ========================================
echo.
echo Backend:  http://localhost:5000
echo Frontend: http://localhost:3000
echo.
echo Press any key to stop all services...
pause >nul

taskkill /FI "WindowTitle eq CloudProof Backend*" /T /F
taskkill /FI "WindowTitle eq CloudProof Frontend*" /T /F
