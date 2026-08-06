import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.scan import EmailScanRequest, EmailScanResponse
from app.services.scan_service import process_email_scan

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email", tags=["Email Scan"])


@router.post("", response_model=EmailScanResponse)
def scan_email(
    req: EmailScanRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return process_email_scan(db, req, user_id=user.id)

    except HTTPException:
        # Penolakan yang disengaja diteruskan apa adanya, jangan diubah
        # jadi 500 - lihat penjelasan lengkapnya di url_scan.py.
        raise

    except Exception:
        # Isi email TIDAK ikut di-log — itu data pribadi milik pengguna.
        # Cukup catat panjangnya untuk keperluan debugging.
        logger.exception(
            "Gagal memindai email (panjang konten: %d karakter)",
            len(req.email_content),
        )
        raise HTTPException(
            status_code=500,
            detail="Terjadi kesalahan internal saat memindai email.",
        )
