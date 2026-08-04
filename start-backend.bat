@echo off
REM ====================================================================
REM  Menjalankan backend ThreatSense.
REM  Klik dua kali berkas ini, atau jalankan dari terminal mana pun.
REM
REM  Berkas ini sengaja TIDAK memakai "activate.bat". Perintah activate
REM  sering gagal diam-diam (kebijakan PowerShell, path dengan spasi),
REM  dan saat gagal, perintah uvicorn berikutnya jadi memakai Python
REM  sistem yang tidak punya paketnya - errornya membingungkan.
REM  Memanggil python.exe di dalam venv secara langsung selalu benar.
REM ====================================================================

cd /d "%~dp0"

set PYTHON=backend\venv\Scripts\python.exe

if not exist "%PYTHON%" (
    echo.
    echo ERROR: Virtual environment tidak ditemukan di:
    echo   %CD%\%PYTHON%
    echo.
    echo Buat dulu dengan perintah:
    echo   python -m venv backend\venv
    echo   backend\venv\Scripts\python.exe -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

"%PYTHON%" run.py --reload %*

pause
