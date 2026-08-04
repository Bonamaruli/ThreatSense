"""
security.py
===========
Pengamanan sandi dan penerbitan token akses.

KENAPA MEMAKAI bcrypt LANGSUNG, BUKAN passlib
---------------------------------------------
Kebanyakan tutorial memakai passlib sebagai pembungkus bcrypt. Di project
ini itu TIDAK bisa: passlib 1.7.4 yang terpasang tidak cocok dengan
bcrypt 5.0.0, dan langsung gagal dengan dua error sekaligus:

    AttributeError: module 'bcrypt' has no attribute '__about__'
    ValueError: password cannot be longer than 72 bytes

passlib mencari nomor versi di tempat yang sudah dihapus bcrypt versi baru.
Karena bcrypt sendiri sudah menyediakan semua yang dibutuhkan, pembungkusnya
tidak dipakai sama sekali - lebih sedikit perantara, lebih sedikit yang bisa
rusak.

CATATAN SOAL BATAS 72 BYTE
--------------------------
bcrypt hanya membaca 72 byte pertama dari sebuah sandi dan mengabaikan
sisanya. Karena itu sandi dipotong secara SENGAJA di sini. Kalau tidak,
bcrypt versi baru justru melempar error, bukan memotong diam-diam.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import settings

# Batas keras dari bcrypt - lihat catatan di atas
_BATAS_BYTE_SANDI = 72


def hash_sandi(sandi: str) -> str:
    """Ubah sandi jadi rangkaian acak yang tidak bisa dikembalikan."""
    b = sandi.encode("utf-8")[:_BATAS_BYTE_SANDI]
    return bcrypt.hashpw(b, bcrypt.gensalt()).decode("utf-8")


def cek_sandi(sandi: str, hash_tersimpan: str) -> bool:
    """
    Cocokkan sandi yang diketik dengan yang tersimpan.

    Dibungkus try/except supaya hash yang rusak atau berformat lama
    mengembalikan False, bukan membuat seluruh permintaan gagal dengan
    error 500 - pembeda yang bisa dipakai penyerang untuk menebak akun
    mana yang ada.
    """
    try:
        return bcrypt.checkpw(
            sandi.encode("utf-8")[:_BATAS_BYTE_SANDI],
            hash_tersimpan.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


def buat_token(user_id: str, email: str) -> str:
    """
    Terbitkan token akses.

    Token memuat id pengguna, jadi setiap permintaan berikutnya bisa tahu
    siapa pemiliknya tanpa perlu mengirim sandi lagi.
    """
    kedaluwarsa = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    isi = {
        "sub": str(user_id),   # 'sub' = subject, penanda baku pemilik token
        "email": email,
        "exp": kedaluwarsa,
    }
    return jwt.encode(isi, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def baca_token(token: str) -> dict | None:
    """
    Buka token dan kembalikan isinya, atau None kalau tidak sah.

    Mengembalikan None (bukan melempar error) supaya pemanggilnya bisa
    memperlakukan token kedaluwarsa, token palsu, dan token acak dengan
    cara yang sama persis: tolak. Membedakan ketiganya lewat pesan error
    justru memberi petunjuk gratis bagi penyerang.
    """
    try:
        return jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except JWTError:
        return None
