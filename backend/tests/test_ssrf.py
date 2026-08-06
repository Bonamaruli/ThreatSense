"""
test_ssrf.py
============
Tes penjagaan terhadap SSRF (Server-Side Request Forgery).

KERENTANAN YANG DIJAGA
Pemindaian mendalam membuka alamat apa pun yang diketik pengguna. Tanpa
penjagaan, server ThreatSense bisa dipakai sebagai perantara untuk
menjangkau tempat yang tidak bisa dicapai penyerang dari luar:

    http://127.0.0.1:8000/     -> layanan internal di server itu sendiri
    http://192.168.1.1/        -> perangkat di jaringan lokal
    http://169.254.169.254/    -> di cloud, alamat ini mengembalikan
                                  kunci akses server

Ini pernah benar-benar bisa: memindai "http://127.0.0.1:8000/health"
mengembalikan status 200. Tes di sini memastikan lubang itu tetap tertutup.

Tes memanggil lapisan penjaganya langsung, bukan lewat endpoint, supaya
tidak perlu koneksi internet dan tetap cepat.
"""

import pytest

from ml.features.jaringan_aman import AlamatDitolak, aman_dibuka, periksa_alamat


class TestAlamatInternalDitolak:
    @pytest.mark.parametrize("url", [
        "http://127.0.0.1:8000/health",     # localhost - kasus aslinya
        "http://127.0.0.1/",
        "http://localhost:8000/",
        "http://0.0.0.0/",
        "http://10.0.0.1/",                 # jaringan privat kelas A
        "http://192.168.1.1/",              # jaringan rumah
        "http://172.16.0.1/",               # jaringan privat kelas B
        "http://169.254.169.254/",          # metadata cloud - paling berbahaya
        "http://[::1]/",                    # localhost IPv6
    ])
    def test_ditolak(self, url):
        aman, alasan = aman_dibuka(url)
        assert aman is False, f"{url} seharusnya ditolak"
        assert alasan, "penolakan harus disertai alasan"


class TestSkemaBerbahayaDitolak:
    @pytest.mark.parametrize("url", [
        "file:///C:/Windows/win.ini",   # membaca berkas di server
        "file:///etc/passwd",
        "gopher://127.0.0.1:8000/",     # mengirim perintah ke layanan internal
        "dict://localhost:11211/",      # menjangkau memcached
        "ftp://internal.local/",
    ])
    def test_ditolak(self, url):
        aman, _ = aman_dibuka(url)
        assert aman is False, f"{url} seharusnya ditolak"

    def test_alasannya_menyebut_skema(self):
        """
        Pesan penolakan harus menyebut sebab yang benar.

        Sempat keliru: "file://" ditolak dengan pesan "Nama host tidak
        terbaca" - hasilnya benar tapi alasannya menyesatkan, dan itu
        menyulitkan siapa pun yang menelusurinya nanti.
        """
        _, alasan = aman_dibuka("file:///etc/passwd")
        assert "http" in alasan.lower()


class TestPortDibatasi:
    def test_port_tidak_lazim_ditolak(self):
        # Port basis data - tidak ada urusannya dengan halaman web
        aman, _ = aman_dibuka("http://contoh.com:5432/")
        assert aman is False

    def test_port_web_umum_diterima(self):
        aman, alasan = aman_dibuka("https://github.com")
        assert aman is True, alasan


class TestAlamatLuarTetapJalan:
    """Penjagaan tidak boleh sampai memblokir alamat yang sah."""

    @pytest.mark.parametrize("url", [
        "https://github.com",
        "https://www.wikipedia.org",
        "http://neverssl.com",
    ])
    def test_diterima(self, url):
        aman, alasan = aman_dibuka(url)
        assert aman is True, f"{url} seharusnya boleh diperiksa: {alasan}"


class TestNamaTidakSah:
    def test_nama_tidak_bisa_diterjemahkan_ditolak(self):
        aman, _ = aman_dibuka("http://domain-yang-pasti-tidak-ada-12345678.com")
        assert aman is False

    def test_periksa_alamat_melempar_pengecualian(self):
        with pytest.raises(AlamatDitolak):
            periksa_alamat("http://127.0.0.1/")
