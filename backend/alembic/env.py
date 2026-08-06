"""
env.py
======
Penghubung antara Alembic dan aplikasi ThreatSense.

DUA HAL YANG SENGAJA DIATUR DI SINI
-----------------------------------
1. Alamat database diambil dari app/config.py, BUKAN ditulis di alembic.ini.

   Kalau ditulis dua kali, cepat atau lambat keduanya akan berbeda - dan
   migrasi bisa berjalan di database yang salah tanpa ada peringatan apa
   pun. Menaruh alamatnya di satu tempat saja menghilangkan kemungkinan itu.

   Sebagai bonus, sandi database tidak pernah tertulis di alembic.ini yang
   ikut masuk git.

2. Seluruh model diimpor agar Alembic bisa membandingkan.

   Alembic mendeteksi perubahan dengan membandingkan isi database terhadap
   Base.metadata. Model yang tidak diimpor tidak akan ada di metadata,
   sehingga Alembic mengira tabelnya harus DIHAPUS - dan migrasi yang
   dihasilkan justru merusak data.
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Daftarkan folder backend/ supaya paket 'app' bisa diimpor saat Alembic
# dijalankan dari folder mana pun.
_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_BACKEND)
for p in (_BACKEND, _ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.config import settings  # noqa: E402
from app.database import Base  # noqa: E402

# WAJIB: mengimpor paket models mendaftarkan SEMUA tabel ke Base.metadata.
# Tanpa baris ini Alembic tidak melihat satu tabel pun.
import app.models  # noqa: E402,F401

config = context.config

# Alamat database diambil dari config aplikasi, menimpa isi alembic.ini
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Hasilkan SQL-nya saja tanpa menyentuh database."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Jalankan migrasi langsung ke database."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # compare_type: ikut mendeteksi perubahan TIPE kolom, bukan cuma
            # kolom yang ditambah atau dihapus. Tanpa ini, mengubah
            # String(50) jadi String(200) tidak akan terdeteksi sama sekali.
            compare_type=True,
            # compare_server_default: mendeteksi perubahan nilai bawaan kolom
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
