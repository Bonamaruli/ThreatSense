"""
feedback.py
===========
Menerima koreksi pengguna saat sistem salah menilai.

KENAPA INI PENTING
------------------
Inilah yang membuat sistem bisa membaik dari waktu ke waktu, bukan berhenti
di kemampuan saat pertama dilatih. Setiap koreksi disimpan bersama fitur
yang dipakai saat itu, sehingga bisa jadi data latih tambahan pada
pelatihan berikutnya.

Nilainya justru terbesar pada kasus yang paling sulit: URL yang membuat
model ragu-ragu. Contoh yang benar-benar sulit jauh lebih berguna untuk
belajar daripada ribuan contoh mudah yang sudah pasti benar.

YANG DIJAGA DI SINI
-------------------
Koreksi hanya boleh diberikan pada riwayat MILIK SENDIRI. Tanpa penjagaan
itu, siapa pun bisa mengirim koreksi palsu secara massal dan meracuni data
latih - model berikutnya justru jadi lebih buruk. Serangan semacam ini
punya nama sendiri di keamanan ML: data poisoning.
"""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.threat import ScanFeedback, ScanHistory
from app.models.user import User
from app.schemas.feedback import FeedbackRequest, FeedbackResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["Koreksi"])


@router.post("", response_model=FeedbackResponse,
             status_code=status.HTTP_201_CREATED)
def kirim_koreksi(
    req: FeedbackRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Simpan koreksi pengguna atas satu hasil pemindaian."""
    scan = (
        db.query(ScanHistory)
        .filter(ScanHistory.id == req.scan_id, ScanHistory.user_id == user.id)
        .first()
    )
    if scan is None:
        # 404, bukan 403 - lihat alasannya di routers/scan_item.py
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Riwayat tidak ditemukan.",
        )

    # Satu pemindaian cukup satu koreksi. Kalau dikirim lagi, yang lama
    # diperbarui - bukan ditumpuk. Tanpa ini, satu orang bisa mengirim
    # ratusan koreksi untuk URL yang sama dan membuatnya seolah jadi bukti
    # terkuat saat pelatihan ulang.
    lama = (
        db.query(ScanFeedback)
        .filter(ScanFeedback.scan_id == scan.id)
        .first()
    )

    if lama:
        lama.user_correction = req.koreksi
        lama.ml_prediction = scan.risk_score
        db.commit()
        db.refresh(lama)
        baris = lama
        baru = False
    else:
        baris = ScanFeedback(
            id=uuid.uuid4(),
            scan_id=scan.id,
            ml_prediction=scan.risk_score,
            user_correction=req.koreksi,
        )
        db.add(baris)
        db.commit()
        db.refresh(baris)
        baru = True

    logger.info(
        "Koreksi %s untuk %s: sistem bilang %s (%.2f), pengguna bilang %s",
        "baru" if baru else "diperbarui",
        scan.input_value[:60], scan.threat_label, scan.risk_score, req.koreksi,
    )

    return FeedbackResponse(
        id=baris.id,
        scan_id=scan.id,
        koreksi=req.koreksi,
        penilaian_sistem=scan.threat_label,
        skor_sistem=scan.risk_score,
        pesan=(
            "Terima kasih. Koreksi ini disimpan dan akan dipakai sebagai "
            "bahan pelatihan model berikutnya."
        ),
    )


@router.get("/statistik")
def statistik_koreksi(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Ringkasan koreksi milik pengguna ini.

    Berguna untuk melihat seberapa sering sistem meleset, dan ke arah mana
    kesalahannya condong.
    """
    baris = (
        db.query(ScanFeedback, ScanHistory)
        .join(ScanHistory, ScanFeedback.scan_id == ScanHistory.id)
        .filter(ScanHistory.user_id == user.id)
        .all()
    )

    total = len(baris)
    # Sistem bilang bahaya, pengguna bilang sebenarnya aman
    salah_alarm = sum(
        1 for f, s in baris
        if f.user_correction == "safe" and s.threat_label != "Safe"
    )
    # Sistem bilang aman, pengguna bilang sebenarnya berbahaya
    kecolongan = sum(
        1 for f, s in baris
        if f.user_correction == "malicious" and s.threat_label == "Safe"
    )

    return {
        "total_koreksi": total,
        "salah_alarm": salah_alarm,
        "kecolongan": kecolongan,
        "keterangan": (
            "salah_alarm = situs aman yang divonis bahaya. "
            "kecolongan = ancaman yang lolos dinilai aman. "
            "Keduanya jadi bahan pelatihan model berikutnya."
        ),
    }
