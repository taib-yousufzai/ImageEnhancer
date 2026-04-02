@echo off
setlocal enabledelayedexpansion

echo.
echo ===================================================
echo   AI Image Enhancer - Full Installation Script
echo ===================================================
echo.

:: 1. Check for Python
echo [*] Checking for Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python is not installed.
    echo [*] Attempting to install Python via winget...
    winget install Python.Python.3.10 --silent --accept-package-agreements --accept-source-agreements
    if !errorlevel! neq 0 (
        echo [!] Automated install failed. Please install Python manually from: https://www.python.org/downloads/
        pause
        exit /b 1
    )
    echo [+] Python installed successfully. Please restart this script after it finishes!
) else (
    echo [+] Python is ready.
)

:: 2. Check for Node.js
echo [*] Checking for Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Node.js is not installed.
    echo [*] Attempting to install Node.js via winget...
    winget install OpenJS.NodeJS --silent --accept-package-agreements --accept-source-agreements
    if !errorlevel! neq 0 (
        echo [!] Automated install failed. Please install Node.js manually from: https://nodejs.org/
        pause
        exit /b 1
    )
    echo [+] Node.js installed successfully.
) else (
    echo [+] Node.js is ready.
)

:: 3. Install Python Dependencies
echo.
echo [*] Installing Python dependencies (pip)...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [!] Failed to install Python dependencies.
    pause
    exit /b 1
)
echo [+] Python dependencies installed.

:: 4. Install Node.js Dependencies
echo.
echo [*] Installing Node.js dependencies (npm)...
call npm install
if %errorlevel% neq 0 (
    echo [!] Failed to install Node.js dependencies.
    pause
    exit /b 1
)
echo [+] Node.js dependencies installed.

:: 5. Download AI Model Weights
echo.
echo [*] Downloading AI Model Weights (this may take a few minutes)...
python download_x2_model.py
python download_x4_model.py
if %errorlevel% neq 0 (
    echo [!] Warning: Model download might have failed or partially succeeded.
    echo [!] Please check the 'models' folder.
) else (
    echo [+] AI Models downloaded.
)

echo.
echo ===================================================
echo   INSTALLATION COMPLETE!
echo ===================================================
echo.
echo You can now use 'run.bat' to start the application.
echo.
pause
