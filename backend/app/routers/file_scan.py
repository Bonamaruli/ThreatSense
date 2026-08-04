import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.config import settings
from app.schemas.scan import FileScanRequest, FileScanResponse
from app.services.scan_service import process_file_scan

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/file", tags=["File Scan"])

# Ukuran potongan saat membaca file (1 MB per potong).
# Kita baca bertahap, bukan sekaligus, supaya bisa berhenti di tengah jalan
# begitu ukurannya melewati batas — RAM server tidak ikut membengkak.
CHUNK_SIZE = 1024 * 1024


async def _read_with_limit(file: UploadFile, max_bytes: int) -> bytes:
    """
    Baca isi file sambil menghitung ukurannya.

    Kenapa tidak pakai `await file.read()` langsung: perintah itu menelan
    SELURUH file ke memori dulu, baru kita bisa cek ukurannya — sudah
    terlambat. Kalau ada yang mengunggah file 5 GB, server kehabisan RAM
    sebelum sempat menolak. Di sini kita berhenti begitu batas terlampaui.
    """
    chunks: list[bytes] = []
    total = 0

    while True:
        chunk = await file.read(CHUNK_SIZE)
        if not chunk:
            break

        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(
                status_code=413,  # 413 = Payload Too Large
                detail=(
                    f"Ukuran file melebihi batas "
                    f"{max_bytes // (1024 * 1024)} MB."
                ),
            )
        chunks.append(chunk)

    if total == 0:
        raise HTTPException(status_code=400, detail="File kosong.")

    return b"".join(chunks)


@router.post("", response_model=FileScanResponse)
async def scan_file(
    file: UploadFile = File(...),
    filename_hint: str | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Tolak tipe file yang tidak diizinkan SEBELUM isinya dibaca.
    # Catatan: content_type dikirim oleh klien jadi bisa dipalsukan — ini
    # saringan awal, bukan jaminan. Verifikasi magic bytes menyusul saat
    # ekstraktor fitur file dibuat.
    if file.content_type not in settings.ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=415,  # 415 = Unsupported Media Type
            detail=(
                f"Tipe file '{file.content_type}' tidak diizinkan. "
                f"Yang diizinkan: {', '.join(settings.ALLOWED_FILE_TYPES)}"
            ),
        )

    file_bytes = await _read_with_limit(file, settings.MAX_FILE_SIZE)
    filename = filename_hint or file.filename or "unknown_file"

    try:
        req = FileScanRequest(filename_hint=filename_hint)
        return process_file_scan(db, filename, file_bytes, req, user_id=user.id)
    except Exception:
        # Pesan asli hanya masuk log server, tidak dikirim ke klien —
        # detail internal (path folder, struktur query) bisa dipakai
        # penyerang untuk memetakan sistem.
        logger.exception("Gagal memindai file: %s", filename)
        raise HTTPException(
            status_code=500,
            detail="Terjadi kesalahan internal saat memindai file.",
        )
