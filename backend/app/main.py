import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.config import settings

# PENTING: impor paket models tetap diperlukan.
# Alembic membandingkan database terhadap Base.metadata, dan model yang
# tidak pernah diimpor tidak akan ada di sana - Alembic akan mengira
# tabelnya harus DIHAPUS, lalu menghasilkan migrasi yang merusak data.
# Sebelumnya baris ini tidak ada dan tabel tetap terbuat — tapi hanya
# kebetulan, lewat rantai impor router -> scan_service -> models.threat.
# Kalau suatu saat rantai itu berubah, tabel diam-diam tidak dibuat.
# Impor eksplisit di sini membuatnya tidak lagi bergantung pada kebetulan.
import app.models  # noqa: F401

from .routers import (
    auth, url_scan, email_scan, file_scan, dashboard, scan_item, feedback,
)

# Nyalakan logging supaya logger.exception() di router benar-benar tercetak
# di terminal. Tanpa ini, error internal tertelan tanpa jejak — sementara
# klien hanya menerima pesan umum, jadi tidak ada yang tahu apa yang rusak.
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

# Diamkan pustaka pihak ketiga yang terlalu cerewet saat DEBUG menyala.
# Tanpa ini, satu kali pemindaian menghasilkan puluhan baris log kunci berkas
# dan httpx, sehingga pesan error kita sendiri tenggelam dan tidak terlihat.
for _bising in ("filelock", "asyncio", "httpx", "httpcore", "urllib3", "matplotlib"):
    logging.getLogger(_bising).setLevel(logging.WARNING)

# Pembuatan tabel otomatis SENGAJA DIMATIKAN.
#
# create_all() hanya MEMBUAT tabel yang belum ada - dia tidak pernah
# mengubah tabel yang sudah terlanjur ada. Akibatnya perubahan model hanya
# terpasang di komputer yang databasenya masih kosong, sementara di komputer
# lain tidak terjadi apa-apa, tanpa satu pun pesan error.
#
# Itu benar-benar terjadi di project ini dan baru ketahuan saat Alembic
# dipasang: kolom input_value sudah jadi Text di model tapi masih
# VARCHAR(1000) di database, dan TIGA indeks (scan_type, threat_label,
# created_at) tidak pernah terbuat - sehingga setiap penyaringan riwayat
# memindai seluruh tabel.
#
# Sekarang struktur tabel HANYA diubah lewat migrasi:
#     backend\venv\Scripts\python.exe -m alembic upgrade head
_ = (Base, engine)  # tetap diimpor karena dipakai bagian lain

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Muat model ML sekali saat server menyala.

    Tanpa ini, model baru dimuat saat permintaan PERTAMA datang - dan
    pengguna pertama menunggu 1,2 detik, sementara permintaan berikutnya
    cuma 0,12 detik. Memindahkan pemuatan ke sini membuat beban itu
    ditanggung saat start, bukan oleh pengguna.
    """
    log = logging.getLogger(__name__)
    try:
        from ml.scoring.url import _muat_model, _muat_daftar_putih
        _, _, nama = _muat_model()
        jml = len(_muat_daftar_putih())
        log.info("Model '%s' dimuat, daftar putih %d domain.", nama, jml)
    except Exception:
        # Server tetap boleh menyala walau model gagal dimuat, supaya
        # endpoint lain (dashboard, riwayat) tidak ikut mati. Pemindaian URL
        # akan mengembalikan error 500 yang tercatat di log.
        log.exception("Model gagal dimuat - endpoint scan URL tidak akan jalan.")

    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Multi-Vector Malicious Content Detection",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes dengan prefix /api/v1 agar cocok dengan frontend
app.include_router(auth.router, prefix="/api/v1")
app.include_router(url_scan.router, prefix="/api/v1/scan")
app.include_router(email_scan.router, prefix="/api/v1/scan")
app.include_router(file_scan.router, prefix="/api/v1/scan")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(feedback.router, prefix="/api/v1")

# Didaftarkan PALING AKHIR. Router ini memuat rute dinamis /scan/{scan_id},
# yang akan menelan /scan/url dan /scan/email kalau didaftarkan lebih dulu -
# FastAPI mencocokkan rute sesuai urutan pendaftaran.
app.include_router(scan_item.router, prefix="/api/v1")


@app.get("/")
def root():
    return {"status": f"{settings.APP_NAME} is running", "version": settings.APP_VERSION}


@app.get("/health")
def health():
    return {"status": "healthy", "service": settings.APP_NAME}
