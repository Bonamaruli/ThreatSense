"""
test_rate_limit.py
==================
Tes pembatas laju permintaan.

Pembatas diuji langsung, bukan lewat endpoint pemindaian mendalam - endpoint
itu membuka koneksi internet sungguhan, jadi tesnya akan lambat dan gagal
saat jaringan bermasalah karena sebab yang tidak ada hubungannya dengan
kode ini.
"""

import time

import pytest

from app.core.rate_limit import BATAS_MENDALAM_PER_MENIT, PembatasLaju, pembatas_mendalam


@pytest.fixture(autouse=True)
def bersihkan():
    """Setiap tes mulai dari catatan kosong supaya tidak saling mengganggu."""
    pembatas_mendalam.reset()
    yield
    pembatas_mendalam.reset()


class TestBatasDasar:
    def test_dalam_batas_diizinkan(self):
        p = PembatasLaju(batas=3)
        for i in range(3):
            boleh, _ = p.periksa("andi")
            assert boleh is True, f"permintaan ke-{i+1} seharusnya boleh"

    def test_melewati_batas_ditolak(self):
        p = PembatasLaju(batas=3)
        for _ in range(3):
            p.periksa("andi")

        boleh, tunggu = p.periksa("andi")
        assert boleh is False
        assert tunggu >= 1, "penolakan harus memberi tahu berapa lama menunggu"

    def test_antar_pengguna_terpisah(self):
        """
        Jatah dihitung per akun.

        Kalau tidak terpisah, satu pengguna yang boros bisa menghabiskan
        jatah semua orang - dan yang lain ikut terblokir tanpa berbuat apa-apa.
        """
        p = PembatasLaju(batas=2)
        p.periksa("andi")
        p.periksa("andi")
        assert p.periksa("andi")[0] is False

        boleh, _ = p.periksa("budi")
        assert boleh is True, "jatah budi tidak boleh ikut habis"


class TestJendelaGeser:
    def test_jatah_pulih_setelah_jendela_lewat(self):
        p = PembatasLaju(batas=2, jendela=1)   # jendela 1 detik supaya tes cepat
        p.periksa("andi")
        p.periksa("andi")
        assert p.periksa("andi")[0] is False

        time.sleep(1.1)
        boleh, _ = p.periksa("andi")
        assert boleh is True, "setelah jendela lewat, jatah harus pulih"

    def test_pemulihan_bertahap_bukan_sekaligus(self):
        """
        Jendela geser, bukan hitung ulang tiap awal periode.

        Kalau memakai hitung ulang, pengguna bisa memakai jatah penuh di
        ujung periode lalu jatah penuh lagi di awal periode berikutnya -
        dua kali lipat dalam waktu sangat singkat.
        """
        p = PembatasLaju(batas=2, jendela=2)
        p.periksa("andi")
        time.sleep(1.2)
        p.periksa("andi")
        assert p.periksa("andi")[0] is False

        # Yang pertama sudah kedaluwarsa, jadi satu slot terbuka - bukan dua
        time.sleep(1.0)
        assert p.periksa("andi")[0] is True
        assert p.periksa("andi")[0] is False


class TestSlotBersamaan:
    """
    Pembatas jumlah yang berjalan BERSAMAAN.

    Pembatas per menit saja tidak cukup: 13 permintaan serentak pernah
    membuat seluruh API berhenti menjawab, karena tiap pemindaian mendalam
    menahan satu thread pekerja selama 3-13 detik.
    """

    def test_slot_habis_ditolak_dengan_429(self):
        from fastapi import HTTPException

        from app.core.rate_limit import MAKS_MENDALAM_BERSAMAAN, SlotMendalam

        dipegang = []
        try:
            for _ in range(MAKS_MENDALAM_BERSAMAAN):
                s = SlotMendalam()
                s.__enter__()
                dipegang.append(s)

            # Slot berikutnya harus ditolak, bukan mengantre
            with pytest.raises(HTTPException) as info:
                SlotMendalam().__enter__()
            assert info.value.status_code == 429
        finally:
            for s in dipegang:
                s.__exit__(None, None, None)

    def test_slot_dikembalikan_setelah_selesai(self):
        from app.core.rate_limit import MAKS_MENDALAM_BERSAMAAN, SlotMendalam

        for _ in range(MAKS_MENDALAM_BERSAMAAN + 3):
            with SlotMendalam():
                pass  # keluar dari 'with' harus mengembalikan slotnya


class TestPenolakanTidakJadi500:
    """
    Penolakan yang disengaja harus sampai ke pengguna apa adanya.

    Bug nyata yang pernah terjadi: HTTPException 429 dilempar di dalam blok
    'try' yang menangkap semua Exception, sehingga berubah jadi 500. Dari 14
    permintaan bersamaan, 6 menerima "kesalahan internal" padahal seharusnya
    "server sedang sibuk" - pesan yang membuat pengguna mengira aplikasinya
    rusak, dan menyesatkan siapa pun yang menelusuri lognya.
    """

    def test_email_terlalu_besar_dijawab_422_bukan_500(self, client, buat_akun):
        akun = buat_akun()
        r = client.post("/api/v1/scan/email", headers=akun["headers"],
                        json={"email_content": "x" * 2_000_000})
        assert r.status_code == 422

    def test_tipe_file_ditolak_415_bukan_500(self, client, buat_akun):
        akun = buat_akun()
        r = client.post("/api/v1/scan/file", headers=akun["headers"],
                        files={"file": ("a.exe", b"MZ\x90\x00", "application/x-msdownload")})
        assert r.status_code == 415


class TestNilaiBawaan:
    def test_batas_mendalam_masuk_akal(self):
        """
        Pemindaian mendalam butuh 3-13 detik. Batas yang terlalu longgar
        membuat pembatasnya tidak ada gunanya; terlalu ketat mengganggu
        pemakaian wajar.
        """
        assert 5 <= BATAS_MENDALAM_PER_MENIT <= 30
