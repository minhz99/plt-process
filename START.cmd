@echo off
cd /d "%~dp0"

call .venv\Scripts\activate.bat

echo Starting PLT Process Server...
waitress-serve --host=0.0.0.0 --port=5525 app:app

pause