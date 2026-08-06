"""
rate_limit.py
=============
Pembatas laju permintaan per akun.

KENAPA PERLU
------------
Pemindaian mendalam membuka koneksi ke internet dan butuh 3-13 detik. Tanpa
pembatas, satu akun bisa mengirim ratusan permintaan sekaligus dan:

  - menghabiskan semua thread pekerja, sehingga pengguna lain ikut macet
  - membuat alamat IP server diblokir penyedia WHOIS karena dianggap
    menyalahgunakan layanan
  - membanjiri situs yang diperiksa - itu tidak sopan, dan bisa dianggap
    serangan oleh pemilik situsnya

Nilai RATE_LIMIT_PER_MINUTE sudah lama ada di config.py tapi tidak pernah
dipakai sama sekali. Berkas ini yang akhirnya memakainya.

CARA KERJANYA: JENDELA GESER
----------------------------
Waktu setiap permintaan dicatat. Saat permintaan baru datang, catatan yang
lebih tua dari satu menit dibuang, lalu sisanya dihitung.

Cara ini dipilih ketimbang "hitung ulang tiap awal menit" karena yang
belakangan punya celah: pengguna bisa mengirim jatah penuh di detik ke-59
lalu jatah penuh lagi di detik ke-01, jadi dua kali lipat dalam dua detik.

BATASAN YANG DIAKUI TERBUKA
---------------------------
Catatan disimpan di MEMORI proses ini saja. Kalau nanti backend dijalankan
lebih dari satu proses, tiap proses punya hitungannya sendiri sehingga batas
sesungguhnya jadi berlipat. Untuk itu perlu penyimpanan bersama seperti
Redis - sudah ada di requirements tapi belum dipakai. Ditulis di sini supaya
tidak terlupa saat naik ke tahap produksi.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, status

# Pemindaian mendalam jauh lebih mahal daripada pemindaian biasa, jadi
# jatahnya dipisah dan dibuat lebih ketat.
BATAS_MENDALAM_PER_MENIT = 10

_JENDELA_DETIK = 60


class PembatasLaju:
    """Pembatas sederhana berbasis jendela geser, aman dipakai banyak thread."""

    def __init__(self, batas: int, jendela: int = _JENDELA_DETIK):
        self.batas = batas
        self.jendela = jendela
        self._catatan: dict[str, deque[float]] = defaultdict(deque)
        # FastAPI menjalankan endpoint biasa di beberapa thread sekaligus,
        # jadi catatannya bisa diubah dua thread pada saat bersamaan.
        self._kunci = threading.Lock()

    def periksa(self, kunci: str) -> tuple[bool, int]:
        """
        Catat satu permintaan.

        Returns:
            (boleh_lanjut, detik_sampai_boleh_lagi)
        """
        sekarang = time.monotonic()
        batas_lama = sekarang - self.jendela

        with self._kunci:
            antrean = self._catatan[kunci]

            while antrean and antrean[0] < batas_lama:
                antrean.popleft()

            if len(antrean) >= self.batas:
                tunggu = int(antrean[0] + self.jendela - sekarang) + 1
                return False, max(tunggu, 1)

            antrean.append(sekarang)

            # Bersihkan kunci yang sudah tidak aktif supaya penggunaan memori
            # tidak terus menumpuk seiring bertambahnya pengguna.
            if len(self._catatan) > 10_000:
                for k in [k for k, v in self._catatan.items() if not v]:
                    del self._catatan[k]

            return True, 0

    def reset(self) -> None:
        """Kosongkan seluruh catatan. Dipakai tes supaya tidak saling ganggu."""
        with self._kunci:
            self._catatan.clear()


# Satu pembatas khusus untuk pemindaian mendalam
pembatas_mendalam = PembatasLaju(BATAS_MENDALAM_PER_MENIT)


# ============================================================
# PEMBATAS JUMLAH YANG BERJALAN BERSAMAAN
# ============================================================
# Pembatas per menit saja TIDAK CUKUP, dan itu terbukti saat pengujian:
# 13 pemindaian mendalam yang dikirim BERSAMAAN membuat seluruh API berhenti
# menjawab - login dan pemindaian cepat ikut macet, padahal keduanya tidak
# ada hubungannya.
#
# Sebabnya: endpoint biasa di FastAPI dijalankan di kumpulan thread yang
# jumlahnya terbatas. Satu pemindaian mendalam menahan satu thread selama
# 3-13 detik menunggu jaringan. Cukup banyak yang berjalan bersamaan, semua
# thread habis dan permintaan lain tidak kebagian.
#
# Pembatas per menit tidak menolong di sini karena masalahnya bukan berapa
# banyak per menit, melainkan berapa banyak PADA SAAT YANG SAMA - dan itu
# juga bisa datang dari banyak pengguna berbeda sekaligus.
MAKS_MENDALAM_BERSAMAAN = 4

_slot_mendalam = threading.Semaphore(MAKS_MENDALAM_BERSAMAAN)


class SlotMendalam:
    """
    Penjaga jumlah pemindaian mendalam yang boleh berjalan bersamaan.

    Dipakai sebagai context manager:

        with SlotMendalam():
            ...pemindaian mendalam...

    Kalau semua slot sedang terpakai, permintaan ditolak dengan 429 - bukan
    dibiarkan antre. Membiarkannya antre justru membuat pengguna menunggu
    lama tanpa kabar, lalu putus sendiri karena batas waktu.
    """

    def __enter__(self):
        if not _slot_mendalam.acquire(blocking=False):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    "Server sedang menangani beberapa pemeriksaan mendalam "
                    "sekaligus. Coba lagi sebentar lagi."
                ),
                headers={"Retry-After": "15"},
            )
        return self

    def __exit__(self, *exc):
        _slot_mendalam.release()
        return False


def batasi_mendalam(user_id) -> None:
    """
    Terapkan batas untuk pemindaian mendalam. Melempar 429 bila terlampaui.

    Dihitung per AKUN, bukan per alamat IP. Alamat IP bisa dibagi banyak
    orang (satu kantor, satu kampus, satu operator seluler), sehingga
    membatasi per IP akan menghukum orang yang tidak bersalah.
    """
    boleh, tunggu = pembatas_mendalam.periksa(str(user_id))
    if not boleh:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Terlalu banyak pemeriksaan mendalam. Setiap akun dibatasi "
                f"{BATAS_MENDALAM_PER_MENIT} kali per menit karena tiap "
                f"pemeriksaan membuka koneksi ke situs yang dituju. "
                f"Coba lagi dalam {tunggu} detik."
            ),
            headers={"Retry-After": str(tunggu)},
        )
