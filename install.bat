@echo off
echo ========================================
echo   WorkforceAI Installation (Windows)
echo ========================================
echo.
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed.
    exit /b 1
)
echo Creating virtual environment...
python -m venv venv
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.
echo Creating directories...
if not exist data mkdir data
if not exist uploads mkdir uploads
if not exist reports mkdir reports
if not exist models mkdir models
echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo "Launching...(Please Wait)"
python app.py
echo.
pause
