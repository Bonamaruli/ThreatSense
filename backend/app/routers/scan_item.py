"""
scan_item.py
============
Endpoint untuk satu baris riwayat: melihat rincian dan menghapus.

Keduanya WAJIB memeriksa kepemilikan. Tanpa pemeriksaan itu, siapa pun yang
punya akun bisa menebak id milik orang lain dan membaca atau menghapusnya -
kelemahan yang sangat umum dan sering lolos karena endpointnya "kelihatan
sudah aman" hanya karena menuntut token.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.threat import ScanHistory
from app.models.user import User
from app.schemas.scan import ScanResultBase

router = APIRouter(prefix="/scan", tags=["Riwayat"])


def _ambil_milik_sendiri(db: Session, scan_id: uuid.UUID, user: User) -> ScanHistory:
    """
    Cari satu baris riwayat milik pengguna ini.

    Baris milik orang lain dijawab 404, BUKAN 403. Menjawab 403 sama saja
    memberi tahu "id ini ada, tapi bukan punyamu" - dan itu cukup untuk
    memetakan isi tabel orang lain. Dengan 404, tidak ada bedanya antara
    "tidak ada" dan "bukan punyamu".
    """
    baris = (
        db.query(ScanHistory)
        .filter(ScanHistory.id == scan_id, ScanHistory.user_id == user.id)
        .first()
    )
    if baris is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Riwayat tidak ditemukan.",
        )
    return baris


@router.get("/{scan_id}", response_model=ScanResultBase)
def detail_scan(
    scan_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Rincian satu hasil scan milik sendiri."""
    return ScanResultBase.model_validate(_ambil_milik_sendiri(db, scan_id, user))


@router.delete("/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
def hapus_scan(
    scan_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Hapus satu riwayat milik sendiri."""
    db.delete(_ambil_milik_sendiri(db, scan_id, user))
    db.commit()
    return None
