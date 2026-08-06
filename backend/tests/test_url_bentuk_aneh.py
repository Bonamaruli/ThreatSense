"""
test_url_bentuk_aneh.py
=======================
Tes alamat yang diketik keliru atau berbentuk aneh.

LATAR BELAKANG
Pengguna mengetik "https:google.com" (kurang dua garis miring) dan seluruh
permintaan gagal dengan 500 Internal Server Error. Penyebabnya berlapis:

  1. Alamat tanpa "://" langsung ditempeli "http://", sehingga jadi
     "http://https:google.com"
  2. Python lalu membaca "https" sebagai nama host dan "google.com" sebagai
     nomor port
  3. Mengakses .port melempar ValueError, bukan mengembalikan None
  4. Error itu menembus sampai ke atas dan mematikan seluruh pemindaian

Yang dilihat pengguna cuma "Terjadi kesalahan internal" - padahal dia hanya
kurang mengetik dua karakter.

Berkas ini menjaga agar tidak ada satu pun bentuk masukan yang bisa
menjatuhkan server. Salah ketik harus diperbaiki diam-diam, dan masukan yang
benar-benar bukan alamat harus ditolak dengan pesan yang bisa dimengerti.
"""

import pytest


class TestSalahKetikDiperbaiki:
    """Salah ketik yang wajar harus tetap bisa dipindai."""

    @pytest.mark.parametrize("url", [
        "https:google.com",       # kurang dua garis miring  <- bug aslinya
        "http:google.com",
        "google.com",             # tanpa skema sama sekali
        "https://google.com",     # sudah benar
        "  https://google.com  ", # ada spasi di ujung
        "HTTPS://GOOGLE.COM",     # huruf besar
        "https://google.com/",    # ada garis miring penutup
    ])
    def test_tetap_bisa_dipindai(self, client, buat_akun, url):
        akun = buat_akun()
        r = client.post("/api/v1/scan/url", json={"url": url},
                        headers=akun["headers"])
        assert r.status_code == 200, f"{url} seharusnya bisa dipindai: {r.text}"

    def test_salah_ketik_dinilai_sama_dengan_bentuk_benarnya(self, client, buat_akun):
        """
        "https:google.com" dan "https://google.com" menunjuk situs yang sama,
        jadi penilaiannya harus sama persis.
        """
        akun = buat_akun()
        salah = client.post("/api/v1/scan/url", json={"url": "https:google.com"},
                            headers=akun["headers"]).json()
        benar = client.post("/api/v1/scan/url", json={"url": "https://google.com"},
                            headers=akun["headers"]).json()

        assert salah["risk_score"] == benar["risk_score"]
        assert salah["threat_label"] == benar["threat_label"]

    def test_daftar_putih_tetap_bekerja_walau_salah_ketik(self, client, buat_akun):
        """
        Penjaga untuk cacat yang sempat ada: fitur dihitung dari alamat yang
        sudah dirapikan, tapi daftar putih masih membaca alamat mentah.
        Akibatnya google.com kehilangan status "domain populer" begitu ada
        salah ketik - diam-diam, tanpa pesan error apa pun.
        """
        akun = buat_akun()
        for url in ["https:google.com", "https:bri.co.id", "http:wikipedia.org"]:
            r = client.post("/api/v1/scan/url", json={"url": url},
                            headers=akun["headers"]).json()
            judul = [e["judul"] for e in r["explanations"]]
            assert "Domain populer" in judul, (
                f"{url} kehilangan status domain populer: {judul}"
            )


class TestMasukanTidakSahDitolak:
    """Masukan yang jelas bukan alamat ditolak dengan sopan, bukan 500."""

    @pytest.mark.parametrize("url", [
        "",
        "   ",
        "!!!",
        "://rusak",
        "http://",
        "bukan alamat sama sekali",
        "12345",
    ])
    def test_ditolak_dengan_422_bukan_500(self, client, buat_akun, url):
        akun = buat_akun()
        r = client.post("/api/v1/scan/url", json={"url": url},
                        headers=akun["headers"])

        # 422 = "masukanmu salah". 500 = "programnya rusak".
        # Bedanya penting: yang satu bisa diperbaiki pengguna, yang satu tidak.
        assert r.status_code == 422, f"{url!r} menghasilkan {r.status_code}"
        assert "500" not in str(r.status_code)

    def test_pesan_penolakan_menjelaskan_dan_memberi_contoh(self, client, buat_akun):
        akun = buat_akun()
        r = client.post("/api/v1/scan/url", json={"url": "!!!"},
                        headers=akun["headers"])
        pesan = r.text.lower()
        assert "contoh" in pesan, "pesan penolakan harus memberi contoh yang benar"


class TestTidakAdaYangBisaMenjatuhkanServer:
    """
    Tidak ada bentuk masukan yang boleh menghasilkan 500.

    Daftar ini sengaja diisi hal-hal aneh. Kalau salah satu menghasilkan 500,
    berarti ada jalur yang belum dijaga.
    """

    @pytest.mark.parametrize("url", [
        "https://contoh.com:99999",          # nomor port di luar batas
        "https://contoh.com:bukanangka",     # port berupa huruf
        "http://pengguna:sandi@contoh.com",  # ada bagian pengguna:sandi
        "https://xn--80ak6aa92e.com",        # punycode
        "https://192.168.1.1",               # alamat IP
        "https://contoh.com/" + "a" * 500,   # path sangat panjang
        "https://" + "sub." * 40 + "contoh.com",  # subdomain bertumpuk
        "https://contoh.com/?x=<script>",    # ada tag di query
    ])
    def test_tidak_pernah_500(self, client, buat_akun, url):
        akun = buat_akun()
        r = client.post("/api/v1/scan/url", json={"url": url},
                        headers=akun["headers"])
        assert r.status_code != 500, f"{url!r} menjatuhkan server: {r.text[:200]}"
