@echo off
setlocal

echo.
echo ==========================================
echo   AI Image Enhancer - Startup Script
echo ==========================================
echo.

:: Start Backend
echo [*] Starting Backend (FastAPI) in a new window...
:: Using 'python -m uvicorn' to ensure it uses the local environment's python
start "AI Enhancer Backend" cmd /k "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

:: Start Frontend
echo [*] Starting Frontend (Next.js) in a new window...
start "AI Enhancer Frontend" cmd /k "npm run dev"

echo.
echo ------------------------------------------
echo [+] Services are starting!
echo API Status: http://localhost:8000/health
echo Frontend:   http://localhost:3000
echo ------------------------------------------
echo.
echo Keep this window open if you want to see this info, 
echo or close it (the servers will stay running).
echo.
pause
