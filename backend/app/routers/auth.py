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
    GantiSandiRequest, LoginRequest, RegisterRequest, TokenResponse,
    UpdateProfilRequest, UserResponse,
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


@router.put("/me", response_model=UserResponse)
def ubah_profil(
    req: UpdateProfilRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Ubah nama dan/atau email milik sendiri.

    Yang diubah SELALU akun pemilik token. Tidak ada parameter id di sini -
    kalau ada, siapa pun bisa mengirim id orang lain dan mengubah akunnya.
    """
    if req.nama is not None:
        user.nama = req.nama.strip()

    if req.email is not None:
        email_baru = req.email.lower().strip()
        if email_baru != user.email:
            bentrok = (
                db.query(User)
                .filter(User.email == email_baru, User.id != user.id)
                .first()
            )
            if bentrok:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email itu sudah dipakai akun lain.",
                )
            user.email = email_baru

    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def ganti_sandi(
    req: GantiSandiRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Ganti sandi. Sandi lama wajib benar."""
    if not cek_sandi(req.sandi_lama, user.hash_sandi):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sandi lama salah.",
        )

    if cek_sandi(req.sandi_baru, user.hash_sandi):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sandi baru tidak boleh sama dengan yang lama.",
        )

    user.hash_sandi = hash_sandi(req.sandi_baru)
    db.commit()

    logger.info("Sandi diganti untuk akun: %s", user.email)

    # CATATAN JUJUR: token yang sudah terbit sebelum ini TETAP berlaku
    # sampai kedaluwarsa sendiri (30 menit). Untuk benar-benar memutus semua
    # sesi lama, perlu daftar token yang dicabut atau nomor versi token di
    # tabel users. Belum dikerjakan - tulis batasan ini di laporan.
    return None
