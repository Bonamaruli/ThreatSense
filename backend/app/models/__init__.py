"""
Kumpulan model database ThreatSense.

Semua model WAJIB diimpor di sini. Alasannya: SQLAlchemy baru "mengenal"
sebuah tabel setelah kelasnya benar-benar diimpor Python. Kalau ada model
yang tidak tercantum di file ini dan kebetulan tidak diimpor dari tempat
lain, Base.metadata.create_all() akan melewatinya diam-diam — tabelnya
tidak pernah dibuat, dan errornya baru muncul jauh belakangan.
"""

from .user import User
from .threat import (
    ScanHistory,
    DomainReputation,
    DomainFeaturesCache,
    FileSignature,
    ScanFeedback,
    ModelVersion,
)

__all__ = [
    "User",
    "ScanHistory",
    "DomainReputation",
    "DomainFeaturesCache",
    "FileSignature",
    "ScanFeedback",
    "ModelVersion",
]
