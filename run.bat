@echo off
echo =========================================================
echo   Starting Verve Bespoke Sub-Second Voice Concierge 🎙️
echo =========================================================
echo.
cd /d "%~dp0"
call .\venv\Scripts\activate.bat
echo Starting FastAPI server on http://localhost:8000 ...
python -m uvicorn server:app --app-dir backend --port 8000 --reload
pause
