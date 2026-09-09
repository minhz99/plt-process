@echo off
cd /d "%~dp0"

call .venv\Scripts\activate.bat

echo ========================================
echo Checking and installing requirements...
echo ========================================

python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ========================================
    echo ERROR: Requirements installation failed!
    echo Server will NOT be started.
    echo ========================================
    pause
    exit /b 1
)

echo.
echo ========================================
echo Requirements OK!
echo Starting PLT Process Server...
echo ========================================

waitress-serve --host=0.0.0.0 --port=5525 --max-request-body-size=10737418240 app:app

pause