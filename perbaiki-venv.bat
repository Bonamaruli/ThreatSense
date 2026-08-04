@echo off
REM ====================================================================
REM  PERBAIKI VIRTUAL ENVIRONMENT SETELAH FOLDER PROJECT DIPINDAH
REM
REM  KAPAN BERKAS INI DIPAKAI
REM  Kalau muncul pesan seperti ini saat menjalankan uvicorn / pip:
REM
REM      Fatal error in launcher: Unable to create process using
REM      '"C:\path\LAMA\venv\Scripts\python.exe" ...'
REM
REM  KENAPA BISA TERJADI
REM  Virtual environment TIDAK BISA dipindah folder. Setiap berkas .exe
REM  di venv\Scripts\ (uvicorn.exe, pip.exe, celery.exe, dan 34 lainnya)
REM  menyimpan path lengkap ke python.exe DI DALAM berkasnya, ditulis
REM  saat paket dipasang. Begitu foldernya pindah, path itu jadi salah
REM  dan semua .exe berhenti bekerja sekaligus.
REM
REM  Yang tetap selamat cuma python.exe sendiri, karena dia tidak
REM  menyimpan path apa pun. Karena itu "python -m uvicorn" tetap jalan
REM  walau "uvicorn" langsung gagal - petunjuk khas masalah ini.
REM
REM  APA YANG DILAKUKAN BERKAS INI
REM  Memasang ulang paket yang punya .exe (tanpa menyentuh paket lain),
REM  supaya berkas .exe-nya ditulis ulang dengan path yang benar.
REM ====================================================================

cd /d "%~dp0"

set PYTHON=backend\venv\Scripts\python.exe

if not exist "%PYTHON%" (
    echo.
    echo ERROR: venv tidak ditemukan di %CD%\%PYTHON%
    echo Buat baru dengan:
    echo   python -m venv backend\venv
    echo   backend\venv\Scripts\python.exe -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo ========================================================
echo Memperbaiki venv yang pindah folder...
echo ========================================================
echo.

echo [1/2] Memperbaiki pip...
"%PYTHON%" -m ensurepip --upgrade
"%PYTHON%" -m pip install --force-reinstall --no-deps pip==24.0

echo.
echo [2/2] Memperbaiki paket yang punya perintah sendiri...
"%PYTHON%" -m pip install --force-reinstall --no-deps ^
    uvicorn==0.30.0 alembic==1.13.0 celery==5.4.0 mlflow==2.16.0

echo.
echo ========================================================
echo SELESAI. Uji dengan:
echo   backend\venv\Scripts\uvicorn.exe --version
echo ========================================================
pause
