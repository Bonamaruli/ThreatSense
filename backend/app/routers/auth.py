"""
auth.py
=======
Endpoint pendaftaran, masuk, dan profil.
"""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import buat_token, cek_sandi, hash_sandi
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    LoginRequest, RegisterRequest, TokenResponse, UserResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Akun"])


@router.post("/register", response_model=TokenResponse,
             status_code=status.HTTP_201_CREATED)
def daftar(req: RegisterRequest, db: Session = Depends(get_db)):
    """Buat akun baru, lalu langsung terbitkan tokennya."""
    email = req.email.lower().strip()

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email ini sudah terdaftar. Silakan masuk saja.",
        )

    user = User(
        id=uuid.uuid4(),
        email=email,
        nama=req.nama.strip(),
        hash_sandi=hash_sandi(req.sandi),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info("Akun baru dibuat: %s", email)

    # Langsung diberi token supaya pengguna tidak perlu mengisi form masuk
    # lagi tepat setelah mendaftar.
    return TokenResponse(
        access_token=buat_token(user.id, user.email),
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
def masuk(req: LoginRequest, db: Session = Depends(get_db)):
    """Periksa email dan sandi, lalu terbitkan token."""
    email = req.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()

    # Email tidak terdaftar dan sandi salah menghasilkan pesan yang SAMA.
    #
    # Kalau dibedakan ("email tidak ditemukan" vs "sandi salah"), siapa pun
    # bisa memakai halaman masuk untuk memeriksa email mana yang punya akun
    # di sini - lalu daftar email itu dipakai untuk serangan yang lebih
    # terarah. Pemeriksaan sandi tetap dijalankan meski penggunanya tidak
    # ada, supaya lama waktu jawabannya tidak ikut membocorkan.
    if user is None:
        cek_sandi(req.sandi, "$2b$12$" + "x" * 53)  # kerja palsu, samakan waktu
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau sandi salah.",
        )

    if not cek_sandi(req.sandi, user.hash_sandi):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau sandi salah.",
        )

    if not user.aktif:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun ini sedang dinonaktifkan.",
        )

    return TokenResponse(
        access_token=buat_token(user.id, user.email),
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def profil_saya(user: User = Depends(get_current_user)):
    """
    Kembalikan data pemilik token.

    Dipakai frontend saat halaman dimuat ulang: token tersimpan di browser,
    tapi nama dan emailnya perlu diambil ulang dari server - jangan pernah
    percaya data profil yang disimpan di sisi browser.
    """
    return UserResponse.model_validate(user)
