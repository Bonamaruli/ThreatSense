"""
file_features.py
================
Analisis STATIS berkas: membaca isinya tanpa pernah menjalankannya.

KENAPA HARUS STATIS
-------------------
Berkas yang diperiksa bisa jadi memang berbahaya. Menjalankannya untuk
melihat apa yang terjadi berarti menginfeksi mesin sendiri. Seluruh
pemeriksaan di sini hanya MEMBACA byte-nya sebagai data:

  - tidak pernah dieksekusi
  - makro Office tidak pernah dijalankan, hanya dideteksi keberadaannya
  - JavaScript di PDF tidak pernah dijalankan, hanya dicari polanya
  - arsip tidak diekstrak ke disk, hanya dibaca daftar isinya

APA YANG DIPERIKSA
------------------
Yang paling menentukan bukan nama berkasnya, melainkan ISI sebenarnya:

  Jenis asli    : dibaca dari magic bytes, bukan dari ekstensi. Berkas
                  bernama "invoice.pdf" yang isinya program Windows adalah
                  temuan besar - dan itu tidak akan pernah terlihat dari
                  namanya.
  Ekstensi ganda: "invoice.pdf.exe" - mata pembaca berhenti di ".pdf"
  Entropi       : isi yang teracak menandakan berkas dipak atau dienkripsi
                  agar tidak terbaca pemindai
  Makro Office  : dokumen yang membawa program di dalamnya
  PDF berbahaya : JavaScript dan perintah yang jalan otomatis saat dibuka
  Hash SHA-256  : sidik jari untuk dicocokkan dengan daftar berkas jahat

Sebelumnya bagian ini hanya menebak dari nama berkas dan ukurannya - sama
sekali tidak membuka isinya.
"""

from __future__ import annotations

import hashlib
import io
import math
import re
import zipfile
from collections import Counter
from typing import Any

# ============================================================
# TANDA PENGENAL JENIS BERKAS (magic bytes)
# ============================================================
# Urutannya penting: pola yang lebih panjang diperiksa lebih dulu supaya
# tidak keburu cocok dengan pola pendek yang mirip.
MAGIC = [
    (b"MZ", "executable-windows", "Program Windows (EXE/DLL)"),
    (b"\x7fELF", "executable-linux", "Program Linux"),
    (b"\xca\xfe\xba\xbe", "executable-mac", "Program macOS"),
    (b"%PDF", "pdf", "Dokumen PDF"),
    (b"PK\x03\x04", "zip", "Arsip ZIP (termasuk dokumen Office modern)"),
    (b"Rar!\x1a\x07", "rar", "Arsip RAR"),
    (b"7z\xbc\xaf\x27\x1c", "7z", "Arsip 7-Zip"),
    (b"\x1f\x8b", "gzip", "Arsip GZIP"),
    (b"\xd0\xcf\x11\xe0", "ole", "Dokumen Office lama (DOC/XLS/PPT)"),
    (b"\x89PNG", "image", "Gambar PNG"),
    (b"\xff\xd8\xff", "image", "Gambar JPEG"),
    (b"GIF8", "image", "Gambar GIF"),
    (b"ID3", "media", "Berkas audio MP3"),
    (b"\x00\x00\x00\x18ftyp", "media", "Berkas video MP4"),
]

# Ekstensi yang bisa langsung dijalankan sistem
EKSTENSI_BISA_JALAN = {
    "exe", "dll", "scr", "com", "pif", "cpl", "msi", "msc", "jar",
    "bat", "cmd", "vbs", "vbe", "js", "jse", "wsf", "wsh", "ps1",
    "psm1", "hta", "reg", "lnk", "sh", "app", "deb", "rpm",
}

# Ekstensi yang tampak tidak berbahaya - dipakai penipu di ekstensi ganda
EKSTENSI_TAMPAK_AMAN = {
    "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "jpg",
    "jpeg", "png", "gif", "mp3", "mp4", "zip", "rar", "csv", "rtf",
}

# Jenis berkas yang seharusnya cocok dengan ekstensinya
HARAPAN_EKSTENSI = {
    "pdf": {"pdf"},
    "zip": {"zip", "docx", "xlsx", "pptx", "docm", "xlsm", "pptm", "jar",
            "apk", "odt", "ods", "epub"},
    "ole": {"doc", "xls", "ppt", "msi", "msg"},
    "executable-windows": {"exe", "dll", "scr", "com", "cpl", "ocx", "sys",
                           "msi", "drv"},
    "image": {"png", "jpg", "jpeg", "gif", "bmp", "webp", "ico"},
    "rar": {"rar"},
    "7z": {"7z"},
    "gzip": {"gz", "tgz"},
}

# Pola berbahaya di dalam PDF
POLA_PDF = {
    "javascript": re.compile(rb"/JavaScript|/JS\b", re.I),
    "auto_jalan": re.compile(rb"/OpenAction|/AA\b", re.I),
    "luncurkan": re.compile(rb"/Launch", re.I),
    "sematan": re.compile(rb"/EmbeddedFile", re.I),
    "kirim_form": re.compile(rb"/SubmitForm", re.I),
}

# Nama berkas di dalam dokumen Office yang menandakan adanya makro
JEJAK_MAKRO = ("vbaproject.bin", "vbadata.xml", "macros/")

BATAS_ENTROPI_TINGGI = 7.2   # dari maksimum 8,0


def _entropi(data: bytes) -> float:
    """
    Ukur keacakan isi berkas.

    Berkas biasa punya pola berulang sehingga entropinya rendah. Berkas yang
    dipak, dienkripsi, atau sengaja disamarkan mendekati 8,0 - dan itu sering
    dipakai agar isinya tidak terbaca pemindai.

    Catatan: berkas gambar dan arsip WAJAR punya entropi tinggi karena
    memang sudah termampatkan. Karena itu angka ini tidak pernah dipakai
    sendirian untuk memvonis.
    """
    if not data:
        return 0.0
    freq = Counter(data)
    n = len(data)
    return round(-sum((c / n) * math.log2(c / n) for c in freq.values()), 4)


def _jenis_asli(data: bytes) -> tuple[str, str]:
    """Tentukan jenis berkas dari magic bytes, bukan dari namanya."""
    for tanda, jenis, keterangan in MAGIC:
        if data.startswith(tanda):
            return jenis, keterangan
    # ZIP dengan komentar di depan, atau berkas teks
    if data[:1024].isascii() and b"\x00" not in data[:1024]:
        return "teks", "Berkas teks biasa"
    return "tidak-dikenal", "Jenis tidak dikenali"


def _periksa_office(data: bytes, h: dict) -> None:
    """
    Cari makro di dalam dokumen Office modern (format ZIP).

    Makro adalah program yang ikut di dalam dokumen. Dokumen surat atau
    faktur biasa tidak perlu membawa program - kehadirannya di lampiran
    yang tidak diminta adalah salah satu cara penyebaran malware paling
    umum sampai hari ini.
    """
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            nama = [n.lower() for n in z.namelist()]
            h["jumlah_berkas_arsip"] = len(nama)

            h["ada_makro"] = any(
                any(j in n for j in JEJAK_MAKRO) for n in nama
            )

            # Berkas yang bisa langsung dijalankan di dalam arsip
            bisa_jalan = [
                n for n in nama
                if n.rsplit(".", 1)[-1] in EKSTENSI_BISA_JALAN
            ]
            h["berkas_bisa_jalan_di_arsip"] = len(bisa_jalan)
            if bisa_jalan:
                h["contoh_berkas_bahaya"] = bisa_jalan[0][:80]

            # Arsip yang isinya arsip lagi - dipakai menyulitkan pemindaian
            h["arsip_bertingkat"] = sum(
                1 for n in nama
                if n.rsplit(".", 1)[-1] in ("zip", "rar", "7z", "gz")
            )
    except zipfile.BadZipFile:
        h["arsip_rusak"] = True
    except Exception:
        pass


def _periksa_pdf(data: bytes, h: dict) -> None:
    """Cari JavaScript dan perintah otomatis di dalam PDF."""
    for nama, pola in POLA_PDF.items():
        h[f"pdf_{nama}"] = bool(pola.search(data))


def extract_file_features(nama_berkas: str, data: bytes) -> dict[str, Any]:
    """
    Periksa sebuah berkas tanpa menjalankannya.

    Args:
        nama_berkas: nama asli berkas, dipakai memeriksa kecocokan ekstensi
        data: isi berkas mentah

    Returns:
        dict berisi temuan. Semua kunci selalu ada, supaya pemakainya tidak
        perlu menulis pengecekan "ada tidaknya kunci" di mana-mana.
    """
    h: dict[str, Any] = {
        "nama_berkas": nama_berkas[:255],
        "ukuran_byte": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "md5": hashlib.md5(data).hexdigest(),
        "jenis_asli": None,
        "jenis_keterangan": None,
        "ekstensi": None,
        "ekstensi_cocok_isi": None,
        "ekstensi_ganda": False,
        "ekstensi_ganda_pola": None,
        "bisa_langsung_jalan": False,
        "entropi": 0.0,
        "entropi_tinggi": False,
        "ada_makro": False,
        "arsip_rusak": False,
        "jumlah_berkas_arsip": 0,
        "berkas_bisa_jalan_di_arsip": 0,
        "contoh_berkas_bahaya": None,
        "arsip_bertingkat": 0,
        "pdf_javascript": False,
        "pdf_auto_jalan": False,
        "pdf_luncurkan": False,
        "pdf_sematan": False,
        "pdf_kirim_form": False,
        "berkas_kosong": len(data) == 0,
    }

    if not data:
        return h

    # ---------- Jenis sebenarnya ----------
    jenis, keterangan = _jenis_asli(data)
    h["jenis_asli"] = jenis
    h["jenis_keterangan"] = keterangan

    # ---------- Ekstensi ----------
    bagian = nama_berkas.lower().rsplit(".", 2)
    ekst = bagian[-1] if len(bagian) > 1 else ""
    h["ekstensi"] = ekst or None
    h["bisa_langsung_jalan"] = ekst in EKSTENSI_BISA_JALAN

    # Ekstensi ganda: "invoice.pdf.exe"
    # Mata pembaca berhenti di ".pdf" dan tidak sampai ke ".exe" - trik lama
    # yang masih sangat sering berhasil.
    if len(bagian) >= 3:
        sebelum = bagian[-2]
        if sebelum in EKSTENSI_TAMPAK_AMAN and ekst in EKSTENSI_BISA_JALAN:
            h["ekstensi_ganda"] = True
            h["ekstensi_ganda_pola"] = f".{sebelum}.{ekst}"

    # ---------- Isi cocok dengan ekstensinya? ----------
    harapan = HARAPAN_EKSTENSI.get(jenis)
    if harapan is not None and ekst:
        h["ekstensi_cocok_isi"] = ekst in harapan

    # ---------- Entropi ----------
    # Diambil dari potongan awal saja; untuk berkas besar hasilnya sudah
    # mewakili dan jauh lebih hemat waktu.
    h["entropi"] = _entropi(data[:512 * 1024])
    h["entropi_tinggi"] = h["entropi"] >= BATAS_ENTROPI_TINGGI

    # ---------- Pemeriksaan khusus per jenis ----------
    if jenis == "zip":
        _periksa_office(data, h)
    elif jenis == "pdf":
        _periksa_pdf(data, h)

    return h
