"""
feedback.py
===========
Bentuk data untuk koreksi pengguna.
"""

import uuid
from typing import Literal

from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    scan_id: uuid.UUID = Field(..., description="Id hasil pemindaian yang dikoreksi")

    # Literal, bukan str bebas. Nilai di luar tiga ini langsung ditolak
    # sebelum masuk database. Kalau dibiarkan bebas, data latih akan berisi
    # label yang tidak seragam ("aman", "Aman", "AMAN", "safe ") dan
    # pelatihan ulang jadi berantakan tanpa ada yang menyadarinya.
    koreksi: Literal["safe", "suspicious", "malicious"] = Field(
        ..., description="Penilaian yang menurut pengguna benar"
    )


class FeedbackResponse(BaseModel):
    id: uuid.UUID
    scan_id: uuid.UUID
    koreksi: str
    penilaian_sistem: str
    skor_sistem: float
    pesan: str
