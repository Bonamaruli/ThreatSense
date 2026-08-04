import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.scan import UrlScanRequest, UrlScanResponse
from app.services.scan_service import process_url_scan

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/url", tags=["URL Scan"])


@router.post("", response_model=UrlScanResponse)
def scan_url(
    req: UrlScanRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return process_url_scan(db, req, user_id=user.id)
    except Exception:
        # str(e) TIDAK dikirim ke klien. Pesan error internal sering memuat
        # path folder, nama tabel, atau potongan query — bahan berharga bagi
        # penyerang untuk memetakan sistem. Detail lengkap tetap tercatat di
        # log server lewat logger.exception() (termasuk traceback).
        logger.exception("Gagal memindai URL: %s", req.url)
        raise HTTPException(
            status_code=500,
            detail="Terjadi kesalahan internal saat memindai URL.",
        )
