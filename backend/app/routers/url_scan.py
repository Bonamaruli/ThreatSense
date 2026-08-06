import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.rate_limit import SlotMendalam, batasi_mendalam
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
    # Batas laju hanya untuk pemindaian mendalam. Pemindaian biasa cuma
    # 0,1 detik dan tidak menyentuh jaringan, jadi tidak perlu dibatasi -
    # membatasinya hanya akan mengganggu pemakaian wajar.
    mendalam = getattr(req, "mendalam", False)
    if mendalam:
        batasi_mendalam(user.id)

    try:
        if mendalam:
            # Batasi juga jumlah yang berjalan BERSAMAAN. Tanpa ini, cukup
            # belasan permintaan serentak untuk membuat seluruh API berhenti
            # menjawab - terbukti saat pengujian.
            with SlotMendalam():
                return process_url_scan(db, req, user_id=user.id)
        return process_url_scan(db, req, user_id=user.id)

    except HTTPException:
        # HTTPException adalah penolakan yang SENGAJA dibuat (429 saat slot
        # penuh, misalnya), bukan kerusakan program. Harus diteruskan apa
        # adanya.
        #
        # Tanpa baris ini, penolakan itu tertangkap 'except Exception' di
        # bawah dan berubah jadi 500 - terbukti saat pengujian: 6 dari 14
        # permintaan bersamaan menerima "kesalahan internal", padahal
        # seharusnya "server sedang sibuk, coba lagi". Pesan yang keliru
        # membuat pengguna mengira aplikasinya rusak.
        raise

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
