"""
main.py
=======
Jalan pintas supaya perintah lama tetap bekerja:

    uvicorn main:app --reload

APLIKASI ASLINYA TIDAK ADA DI SINI.
Semua isi aplikasi (routing, CORS, pemuatan model, pembuatan tabel) ada di
backend/app/main.py. Berkas ini cuma menunjuk ke sana.

KENAPA DIBUAT
Aplikasi pernah dipindah dari backend/main.py ke backend/app/main.py.
Setelah pindah, perintah `uvicorn main:app` yang sudah jadi kebiasaan
langsung gagal dengan pesan:

    ERROR: Error loading ASGI app. Could not import module "main".

Berkas satu baris ini membuat perintah lama dan baru sama-sama jalan.

KENAPA INI TIDAK MENGULANG MASALAH LAMA
Dulu ada DUA definisi FastAPI yang berbeda (satu di backend/main.py, satu
di backend/app/main.py), dan tidak jelas mana yang sebenarnya dipakai.
Sekarang definisinya cuma SATU, di app/main.py. Berkas ini tidak membuat
aplikasi baru - dia hanya meneruskan yang sudah ada, jadi tidak mungkin
keduanya berbeda isi.

CATATAN: berkas ini hanya menolong kalau dijalankan DARI DALAM folder
backend/. Kalau ingin bisa dijalankan dari folder mana pun, pakai run.py
di folder root.
"""

from app.main import app  # noqa: F401

__all__ = ["app"]
