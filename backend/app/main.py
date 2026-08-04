import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.config import settings

# PENTING: impor paket models SEBELUM create_all().
# Sebelumnya baris ini tidak ada dan tabel tetap terbuat — tapi hanya
# kebetulan, lewat rantai impor router -> scan_service -> models.threat.
# Kalau suatu saat rantai itu berubah, tabel diam-diam tidak dibuat.
# Impor eksplisit di sini membuatnya tidak lagi bergantung pada kebetulan.
import app.models  # noqa: F401

from .routers import auth, url_scan, email_scan, file_scan, dashboard

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

# Buat tabel jika belum ada.
# CATATAN: perintah ini HANYA membuat tabel yang belum ada. Dia tidak
# mengubah struktur tabel yang sudah terlanjur ada. Untuk mengubah struktur,
# pakai Alembic (lihat catatan di app/models/threat.py).
Base.metadata.create_all(bind=engine)

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
        from ml.predict import _muat_model, _muat_daftar_putih
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


@app.get("/")
def root():
    return {"status": f"{settings.APP_NAME} is running", "version": settings.APP_VERSION}


@app.get("/health")
def health():
    return {"status": "healthy", "service": settings.APP_NAME}
