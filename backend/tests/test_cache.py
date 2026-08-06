"""
test_cache.py
=============
Tes simpanan sementara hasil pemeriksaan domain.

Yang paling penting dijaga di sini: cache TIDAK BOLEH menyimpan isi halaman.
Halaman phishing bisa berubah dalam hitungan jam, dan menyajikan isi halaman
basi justru lebih berbahaya daripada tidak menyimpan sama sekali - pengguna
akan melihat "aman" berdasarkan halaman yang sudah tidak ada lagi.
"""

from datetime import datetime, timedelta, timezone

from app.services import cache_service

BUKTI_CONTOH = {
    # Bagian stabil - boleh disimpan
    "umur_domain_hari": 6875,
    "tanggal_dibuat": "2007-10-09",
    "negara_pendaftar": "US",
    "registrar": "MarkMonitor, Inc.",
    "ip": "20.205.243.166",
    "negara_hosting": "Singapore",
    "kode_negara_hosting": "SG",
    "isp": "Microsoft Corporation",
    "ssl_ada": True,
    "ssl_penerbit": "Sectigo Limited",
    # Bagian berubah-ubah - TIDAK boleh disimpan
    "halaman_terbaca": True,
    "judul_halaman": "Judul yang bisa berubah kapan saja",
    "ada_kolom_sandi": False,
    "status_http": 200,
    "kata_judi_di_halaman": 0,
    "url_akhir": "https://contoh.com/",
}


class TestSimpanDanAmbil:
    def test_belum_ada_mengembalikan_none(self, db_uji):
        assert cache_service.ambil(db_uji, "belum-pernah.com") is None

    def test_tersimpan_lalu_terbaca(self, db_uji):
        cache_service.simpan(db_uji, "contoh.com", BUKTI_CONTOH)
        hasil = cache_service.ambil(db_uji, "contoh.com")

        assert hasil is not None
        assert hasil["umur_domain_hari"] == 6875
        assert hasil["negara_hosting"] == "Singapore"

    def test_domain_kosong_diabaikan(self, db_uji):
        cache_service.simpan(db_uji, "", BUKTI_CONTOH)
        assert cache_service.ambil(db_uji, "") is None


class TestHanyaBagianStabilDisimpan:
    def test_isi_halaman_tidak_ikut_tersimpan(self, db_uji):
        """
        Penjagaan terpenting di berkas ini.

        Isi halaman yang basi akan membuat pengguna melihat penilaian
        berdasarkan halaman yang mungkin sudah berubah total.
        """
        cache_service.simpan(db_uji, "contoh.com", BUKTI_CONTOH)
        hasil = cache_service.ambil(db_uji, "contoh.com")

        for kunci in ("halaman_terbaca", "judul_halaman", "ada_kolom_sandi",
                      "status_http", "kata_judi_di_halaman", "url_akhir"):
            assert kunci not in hasil, (
                f"'{kunci}' berubah-ubah dan tidak boleh disimpan"
            )

    def test_bagian_stabil_lengkap(self, db_uji):
        cache_service.simpan(db_uji, "contoh.com", BUKTI_CONTOH)
        hasil = cache_service.ambil(db_uji, "contoh.com")

        for kunci in ("umur_domain_hari", "negara_pendaftar", "registrar",
                      "ip", "isp", "ssl_penerbit"):
            assert kunci in hasil


class TestKedaluwarsa:
    def test_yang_sudah_kedaluwarsa_tidak_dipakai(self, db_uji):
        from app.models.threat import DomainFeaturesCache

        lampau = datetime.now(timezone.utc) - timedelta(days=1)
        db_uji.add(DomainFeaturesCache(
            domain="basi.com",
            features_json={"umur_domain_hari": 100},
            cached_at=lampau,
            expires_at=lampau,
        ))
        db_uji.commit()

        assert cache_service.ambil(db_uji, "basi.com") is None

    def test_menyimpan_ulang_memperbarui_bukan_menggandakan(self, db_uji):
        from app.models.threat import DomainFeaturesCache

        cache_service.simpan(db_uji, "contoh.com", BUKTI_CONTOH)
        baru = dict(BUKTI_CONTOH, umur_domain_hari=7000)
        cache_service.simpan(db_uji, "contoh.com", baru)

        jumlah = (db_uji.query(DomainFeaturesCache)
                  .filter(DomainFeaturesCache.domain == "contoh.com").count())
        assert jumlah == 1
        assert cache_service.ambil(db_uji, "contoh.com")["umur_domain_hari"] == 7000


class TestKegagalanTidakDisimpan:
    def test_hasil_gagal_tidak_disimpan(self, db_uji):
        """
        Kalau WHOIS sedang bermasalah, kegagalannya jangan ikut tersimpan -
        kalau tersimpan, hasil kosong itu akan terus dipakai selama seminggu
        walau layanannya sudah pulih.
        """
        gagal = {"umur_domain_hari": None, "ip": None, "kegagalan": ["WHOIS mati"]}
        cache_service.simpan(db_uji, "gagal.com", gagal)
        assert cache_service.ambil(db_uji, "gagal.com") is None
