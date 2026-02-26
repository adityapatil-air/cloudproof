@echo off
echo Testing CloudProof API...
echo.

echo [1/3] Health Check...
curl -s http://localhost:5000/api/health
echo.
echo.

echo [2/3] List Users...
curl -s http://localhost:5000/api/users
echo.
echo.

echo [3/3] Create Test User...
curl -X POST http://localhost:5000/api/users -H "Content-Type: application/json" -d "{\"name\":\"Test User\",\"email\":\"test@example.com\",\"role_arn\":\"arn:aws:iam::123456789012:role/TestRole\"}"
echo.
echo.

echo Test complete!
pause
