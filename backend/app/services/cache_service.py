"""
cache_service.py
================
Simpanan sementara hasil pemeriksaan domain.

KENAPA PERLU
------------
Pemeriksaan mendalam memanggil WHOIS, DNS, dan layanan lokasi IP setiap
kali. Untuk domain yang sama, hasilnya praktis tidak berubah dari hari ke
hari - umur domain bertambah satu per hari, negara pendaftaran hampir tidak
pernah berubah.

Mengulang panggilan itu berarti:
  - lambat, padahal jawabannya sudah pernah didapat (WHOIS saja 3-5 detik)
  - server WHOIS dibanjiri permintaan yang sama. Mereka punya batas kuota,
    dan alamat IP yang menyalahgunakannya bisa diblokir - kalau itu terjadi,
    fitur ini mati untuk semua pengguna sekaligus

Tabel domain_features_cache sudah lama dibuat tapi tidak pernah dipakai.
Berkas ini yang akhirnya memakainya.

YANG DISIMPAN DAN YANG TIDAK
----------------------------
Hanya bagian yang STABIL: umur domain, negara pendaftaran, registrar,
lokasi server. Bagian yang berubah-ubah - isi halaman, status HTTP, rantai
pengalihan - TIDAK disimpan dan selalu diambil ulang. Halaman phishing bisa
berubah dalam hitungan jam, dan menyajikan isi halaman basi justru lebih
berbahaya daripada tidak menyimpan sama sekali.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.threat import DomainFeaturesCache

logger = logging.getLogger(__name__)

# Berapa lama hasil dianggap masih layak pakai.
#
# 7 hari dipilih karena data yang disimpan memang jarang berubah. Terlalu
# pendek membuat cache tidak ada gunanya; terlalu panjang membuat umur
# domain yang ditampilkan meleset jauh - dan untuk domain yang baru berumur
# beberapa minggu, selisih itu justru menentukan penilaiannya.
UMUR_CACHE_HARI = 7

# Kunci yang boleh disimpan. Sengaja ditulis sebagai daftar putih, bukan
# daftar hitam: kalau nanti ada kunci baru yang berubah-ubah, ia otomatis
# TIDAK ikut tersimpan tanpa perlu diingat-ingat.
KUNCI_STABIL = (
    "umur_domain_hari",
    "tanggal_dibuat",
    "negara_pendaftar",
    "registrar",
    "ip",
    "negara_hosting",
    "kode_negara_hosting",
    "isp",
    "ssl_ada",
    "ssl_penerbit",
    "ssl_umur_hari",
    "ssl_cocok_domain",
)


def ambil(db: Session, domain: str) -> dict[str, Any] | None:
    """Ambil hasil tersimpan untuk sebuah domain, atau None bila tidak ada."""
    if not domain:
        return None

    try:
        baris = (
            db.query(DomainFeaturesCache)
            .filter(DomainFeaturesCache.domain == domain)
            .first()
        )
    except Exception:
        # Kegagalan membaca cache TIDAK boleh menggagalkan pemindaian.
        # Cache hanya mempercepat; ketiadaannya cuma membuat lebih lambat.
        logger.exception("Gagal membaca cache domain %s", domain)
        return None

    if baris is None:
        return None

    if baris.expires_at and _sudah_lewat(baris.expires_at):
        return None

    return baris.features_json or None


def _sudah_lewat(waktu: datetime) -> bool:
    """
    Benarkah waktu ini sudah lewat?

    Waktu dari database bisa datang DENGAN atau TANPA zona waktu, tergantung
    databasenya. PostgreSQL menyertakan zona; SQLite tidak. Membandingkan
    keduanya langsung akan gagal:

        TypeError: can't compare offset-naive and offset-aware datetimes

    Yang tanpa zona dianggap UTC, karena memang begitu cara menyimpannya di
    sini. Menyamakan dulu membuat kode ini bekerja di kedua database.
    """
    if waktu.tzinfo is None:
        waktu = waktu.replace(tzinfo=timezone.utc)
    return waktu < datetime.now(timezone.utc)


def simpan(db: Session, domain: str, bukti: dict[str, Any]) -> None:
    """Simpan bagian yang stabil dari hasil pemeriksaan."""
    if not domain or not bukti:
        return

    # Jangan simpan hasil yang gagal - kalau WHOIS sedang bermasalah,
    # kegagalannya akan ikut tersimpan dan terus dipakai selama seminggu.
    if bukti.get("umur_domain_hari") is None and bukti.get("ip") is None:
        return

    isi = {k: bukti.get(k) for k in KUNCI_STABIL if bukti.get(k) is not None}
    if not isi:
        return

    sekarang = datetime.now(timezone.utc)
    kedaluwarsa = sekarang + timedelta(days=UMUR_CACHE_HARI)

    try:
        baris = (
            db.query(DomainFeaturesCache)
            .filter(DomainFeaturesCache.domain == domain)
            .first()
        )
        if baris:
            baris.features_json = isi
            baris.cached_at = sekarang
            baris.expires_at = kedaluwarsa
        else:
            db.add(DomainFeaturesCache(
                domain=domain, features_json=isi,
                cached_at=sekarang, expires_at=kedaluwarsa,
            ))
        db.commit()
    except Exception:
        # Sama seperti di atas: gagal menyimpan tidak boleh merusak hasil
        # pemindaian yang sudah benar.
        logger.exception("Gagal menyimpan cache domain %s", domain)
        db.rollback()
