"""
auth.py
=======
Bentuk data untuk pendaftaran, masuk, dan profil pengguna.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    nama: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    # Minimal 8 karakter. Bukan angka sakti, tapi di bawah itu sandi bisa
    # ditebak habis dalam hitungan detik oleh komputer biasa.
    sandi: str = Field(..., min_length=8, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    sandi: str = Field(..., min_length=1, max_length=200)


class UserResponse(BaseModel):
    id: uuid.UUID
    nama: str
    email: EmailStr
    created_at: datetime

    # Perhatikan: hash_sandi TIDAK ada di sini, jadi mustahil ikut terkirim
    # ke browser walau kodenya nanti diubah orang lain.
    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UpdateProfilRequest(BaseModel):
    """Kolom yang boleh diubah pengguna sendiri."""
    nama: str | None = Field(None, min_length=2, max_length=120)
    email: EmailStr | None = None


class GantiSandiRequest(BaseModel):
    """
    Sandi lama WAJIB diisi.

    Alasannya: kalau seseorang meninggalkan browsernya terbuka, siapa pun
    yang lewat bisa mengganti sandi dan mengunci pemilik aslinya. Meminta
    sandi lama memastikan yang mengubah memang pemiliknya.
    """
    sandi_lama: str = Field(..., min_length=1, max_length=200)
    sandi_baru: str = Field(..., min_length=8, max_length=200)
