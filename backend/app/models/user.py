"""
user.py
=======
Tabel pengguna ThreatSense.

Sandi TIDAK PERNAH disimpan apa adanya. Yang tersimpan hanya hasil
pengacakannya (hash bcrypt), yang tidak bisa dikembalikan jadi sandi asli.
Kalau database ini sampai bocor, sandi penggunanya tetap tidak terbaca.
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Email dipakai sebagai identitas masuk, jadi wajib unik.
    # index=True karena setiap kali masuk, baris dicari lewat kolom ini.
    email = Column(String(255), unique=True, nullable=False, index=True)

    nama = Column(String(120), nullable=False)

    # Berisi hash bcrypt, BUKAN sandi asli. Panjangnya 60 karakter,
    # tapi diberi ruang lebih agar tidak perlu migrasi kalau algoritmanya
    # diganti nanti.
    hash_sandi = Column(String(255), nullable=False)

    aktif = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Riwayat scan milik pengguna ini.
    # cascade delete: kalau akun dihapus, riwayatnya ikut terhapus - tidak
    # ada gunanya menyimpan riwayat yang tidak bisa diakses siapa pun lagi.
    scans = relationship(
        "ScanHistory", back_populates="user",
        cascade="all, delete-orphan", passive_deletes=True,
    )

    def __repr__(self):
        return f"<User(email={self.email})>"
