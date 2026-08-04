"""
dependencies.py
===============
Penentu "siapa yang sedang mengirim permintaan ini".

Dipakai FastAPI lewat Depends(). Setiap endpoint yang menuliskannya otomatis
menolak permintaan tanpa token yang sah, jadi pemeriksaannya tidak perlu
ditulis ulang di setiap fungsi - dan tidak bisa lupa ditulis.
"""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import baca_token
from app.database import get_db
from app.models.user import User

# auto_error=False supaya kita sendiri yang menyusun pesan penolakannya,
# bukan memakai pesan bawaan FastAPI yang berbahasa Inggris.
_skema = HTTPBearer(auto_error=False)

_TOLAK = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Sesi tidak sah atau sudah berakhir. Silakan masuk kembali.",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    kredensial: HTTPAuthorizationCredentials | None = Depends(_skema),
    db: Session = Depends(get_db),
) -> User:
    """
    Ambil pengguna pemilik token.

    Semua kegagalan - token tidak ada, kedaluwarsa, palsu, atau menunjuk
    akun yang sudah dihapus - menghasilkan pesan yang SAMA PERSIS. Pesan
    yang berbeda-beda akan memberi tahu penyerang mana yang salah, dan itu
    petunjuk gratis untuk menebak akun mana yang ada.
    """
    if kredensial is None or not kredensial.credentials:
        raise _TOLAK

    isi = baca_token(kredensial.credentials)
    if not isi:
        raise _TOLAK

    user_id = isi.get("sub")
    if not user_id:
        raise _TOLAK

    try:
        user_uuid = uuid.UUID(str(user_id))
    except ValueError:
        raise _TOLAK

    user = db.query(User).filter(User.id == user_uuid).first()
    if user is None or not user.aktif:
        raise _TOLAK

    return user
