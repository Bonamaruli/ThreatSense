"""
test_scan.py
============
Tes mesin pemindaian lewat endpoint.

Yang dijaga di sini bukan angka pastinya (itu bisa bergeser tiap model
dilatih ulang), melainkan PERILAKUNYA: situs terkenal tidak boleh dituduh
berbahaya, dan penipuan yang jelas tidak boleh lolos.
"""

import pytest


def _scan_url(client, headers, url):
    r = client.post("/api/v1/scan/url", json={"url": url}, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


class TestScanUrl:
    @pytest.mark.parametrize("url", [
        "https://github.com/torvalds/linux",
        "https://www.wikipedia.org",
        "https://www.bps.go.id",
    ])
    def test_situs_terkenal_dinilai_aman(self, client, buat_akun, url):
        """
        Penjaga terhadap kesalahan lama: model versi pertama menuduh
        github.com berbahaya 99,97% hanya karena URL-nya punya path.
        """
        akun = buat_akun()
        assert _scan_url(client, akun["headers"], url)["threat_label"] == "Safe"

    @pytest.mark.parametrize("url", [
        "https://slot-gacor-maxwin88.com/daftar",
        "https://bri-mobile-verifikasi.com/login",
        "http://192.168.1.1/bank/verify.html",
    ])
    def test_penipuan_jelas_tidak_lolos(self, client, buat_akun, url):
        akun = buat_akun()
        assert _scan_url(client, akun["headers"], url)["threat_label"] != "Safe"

    def test_path_tidak_mengubah_penilaian(self, client, buat_akun):
        """
        Fitur hanya membaca nama domain. Kalau tes ini gagal, berarti ada
        fitur yang mulai membaca path lagi - pintu masuk kebocoran lama.
        """
        akun = buat_akun()
        a = _scan_url(client, akun["headers"], "https://github.com")
        b = _scan_url(client, akun["headers"], "https://github.com/apa/saja?x=1")
        assert a["risk_score"] == b["risk_score"]

    def test_hasil_selalu_disertai_alasan(self, client, buat_akun):
        akun = buat_akun()
        h = _scan_url(client, akun["headers"], "https://slot-gacor-maxwin88.com")
        assert h["explanations"], "hasil scan wajib menyertakan alasan"
        assert h["explanations"][0]["judul"]
        assert h["explanations"][0]["alasan"]

    def test_skor_selalu_dalam_rentang_wajar(self, client, buat_akun):
        akun = buat_akun()
        for u in ["https://github.com", "https://slot-gacor-maxwin88.com"]:
            skor = _scan_url(client, akun["headers"], u)["risk_score"]
            assert 0.0 <= skor <= 1.0


class TestScanEmail:
    def test_phishing_bank_terdeteksi(self, client, buat_akun):
        akun = buat_akun()
        isi = (
            'From: "Bank BRI" <bri.verifikasi@gmail.com>\n'
            "Reply-To: penampung@mail.ru\n"
            "Subject: SEGERA - Rekening Diblokir\n\n"
            "Segera verifikasi kata sandi dan PIN Anda:\n"
            '<a href="http://bri-verifikasi-nasabah.tk/login">https://bri.co.id</a>'
        )
        r = client.post("/api/v1/scan/email", json={"email_content": isi},
                        headers=akun["headers"])
        assert r.status_code == 200
        d = r.json()
        assert d["threat_label"] == "Malicious"
        assert len(d["explanations"]) >= 3

    def test_email_biasa_tidak_dituduh(self, client, buat_akun):
        akun = buat_akun()
        isi = (
            "From: GitHub <noreply@github.com>\n"
            "Subject: New pull request\n\n"
            "A new pull request was opened.\n"
            "View it: https://github.com/a/b/pull/1"
        )
        r = client.post("/api/v1/scan/email", json={"email_content": isi},
                        headers=akun["headers"])
        assert r.json()["threat_label"] == "Safe"

    def test_isi_email_tidak_disimpan_utuh(self, client, buat_akun):
        """Isi email itu data pribadi - hanya cuplikan yang boleh tersimpan."""
        akun = buat_akun()
        panjang = "Ini kalimat rahasia. " * 40
        r = client.post("/api/v1/scan/email", json={"email_content": panjang},
                        headers=akun["headers"])
        assert len(r.json()["input_value"]) <= 200


class TestKesehatanAplikasi:
    def test_health_terbuka_tanpa_token(self, client):
        """Endpoint kesehatan harus bisa diakses pemantau tanpa masuk."""
        assert client.get("/health").status_code == 200

    def test_dokumentasi_api_tersedia(self, client):
        assert client.get("/docs").status_code == 200
