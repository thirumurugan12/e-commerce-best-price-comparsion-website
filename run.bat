@echo off
cd /d "%~dp0"
echo ================================================
echo   BestPrice India - Starting...
echo ================================================
echo.

if not exist "venv" (
    echo [1/5] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo.
        echo ERROR: Python not found!
        echo Please install Python from https://python.org
        pause & exit /b 1
    )
)

echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/5] Installing packages (first run may take a minute)...
pip install -r requirements.txt -q --no-warn-script-location

echo [4/5] Setting up database...
python manage.py makemigrations --check >nul 2>&1
python manage.py makemigrations store
python manage.py migrate

echo [5/5] Starting server...
echo.
echo ================================================
echo   Open browser:  http://127.0.0.1:8000
echo   Press Ctrl+C to stop
echo ================================================
echo.
python manage.py runserver
pause
