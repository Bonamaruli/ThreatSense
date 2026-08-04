@echo off
REM ====================================================================
REM  Berkas ini dipertahankan supaya kebiasaan lama tetap jalan.
REM  Isinya sekarang cuma meneruskan ke start-backend.bat di folder root.
REM
REM  Versi lamanya menjalankan "uvicorn app.main:app" setelah activate.bat,
REM  dan itu hanya berhasil kalau dijalankan dari dalam folder backend.
REM  Dijalankan dari tempat lain hasilnya selalu:
REM      ModuleNotFoundError: No module named 'app'
REM ====================================================================

cd /d "%~dp0.."
call start-backend.bat %*
