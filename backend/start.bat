@echo off
echo ========================================
echo ThreatSense Backend - Starting...
echo ========================================
echo.

REM Pastikan script berjalan dari folder backend
cd /d "%~dp0"

REM Aktifkan virtual environment
echo [1/2] Activating virtual environment...
call venv\Scripts\activate.bat

REM Jalankan server
echo [2/2] Starting FastAPI server...
echo Server akan berjalan di http://localhost:8000
echo Tekan CTRL+C untuk stop
echo.

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause