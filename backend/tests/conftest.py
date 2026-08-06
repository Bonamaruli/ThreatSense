"""
conftest.py
===========
Persiapan bersama untuk seluruh tes.

PENTING: tes memakai database TERPISAH, bukan database aslimu.

Kalau tes menulis ke database sungguhan, setiap kali dijalankan akan
menambah akun dan riwayat sampah - dan yang lebih buruk, tes yang menghapus
data bisa menghapus datamu. Di sini dipakai SQLite berkas sementara yang
dibuat lalu dibuang setiap sesi tes.

Catatan: model memakai tipe khas PostgreSQL (UUID dan JSONB) yang tidak
dikenal SQLite. Karena itu keduanya diterjemahkan lebih dulu di bawah,
supaya tabelnya tetap bisa dibuat di SQLite.
"""

import os
import sys
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, types
from sqlalchemy.orm import sessionmaker

# Daftarkan folder backend/ dan root project supaya `app` dan `ml` ketemu
_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_BACKEND)
for p in (_BACKEND, _ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.database import Base, get_db  # noqa: E402

# Diberi nama lain (fastapi_app), BUKAN "app".
#
# Baris "import app.models" di bawah mendaftarkan nama `app` sebagai PAKET,
# sehingga variabel `app` yang berisi instance FastAPI ikut tertimpa. Akibatnya
# muncul error yang membingungkan:
#     AttributeError: module 'app' has no attribute 'dependency_overrides'
from app.main import app as fastapi_app  # noqa: E402
import app.models  # noqa: E402,F401


# ============================================================
# Terjemahan tipe PostgreSQL -> SQLite
# ============================================================

class _UUIDSqlite(types.TypeDecorator):
    """Simpan UUID sebagai teks saat berjalan di SQLite."""
    impl = types.CHAR(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return str(value) if value is not None else None

    def process_result_value(self, value, dialect):
        return uuid.UUID(value) if value is not None else None


@pytest.fixture(scope="session")
def engine_uji(tmp_path_factory):
    berkas = tmp_path_factory.mktemp("db") / "uji.sqlite"
    eng = create_engine(f"sqlite:///{berkas}", connect_args={"check_same_thread": False})

    # Ganti tipe khas PostgreSQL pada SALINAN metadata milik sesi tes ini
    from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

    for tabel in Base.metadata.tables.values():
        for kolom in tabel.columns:
            if isinstance(kolom.type, PGUUID):
                kolom.type = _UUIDSqlite()
            elif isinstance(kolom.type, JSONB):
                kolom.type = types.JSON()

    Base.metadata.create_all(bind=eng)
    return eng


@pytest.fixture
def db_uji(engine_uji):
    """Sesi database bersih untuk satu tes."""
    Sesi = sessionmaker(autocommit=False, autoflush=False, bind=engine_uji)
    sesi = Sesi()
    try:
        yield sesi
    finally:
        sesi.close()


@pytest.fixture
def client(db_uji):
    """
    Klien HTTP yang memakai database uji.

    get_db diganti sementara supaya seluruh endpoint memakai sesi uji,
    bukan database sungguhan.
    """
    def _get_db_uji():
        try:
            yield db_uji
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = _get_db_uji
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def buat_akun(client):
    """
    Pabrik akun untuk tes.

    Mengembalikan fungsi yang membuat akun baru dan langsung memberi header
    berisi tokennya, supaya tiap tes tidak perlu menulis ulang alur daftar.
    """
    def _buat(nama="Uji Coba", sandi="sandiRahasia1"):
        email = f"uji-{uuid.uuid4().hex[:10]}@contoh.com"
        r = client.post(
            "/api/v1/auth/register",
            json={"nama": nama, "email": email, "sandi": sandi},
        )
        assert r.status_code == 201, r.text
        data = r.json()
        return {
            "email": email,
            "sandi": sandi,
            "token": data["access_token"],
            "user": data["user"],
            "headers": {"Authorization": "Bearer " + data["access_token"]},
        }

    return _buat
