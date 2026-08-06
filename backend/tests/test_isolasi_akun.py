"""
test_isolasi_akun.py
====================
Tes bahwa riwayat satu akun TIDAK BISA dilihat atau dihapus akun lain.

Ini berkas tes terpenting di project. Kebocoran antar akun tidak
memunculkan error apa pun - aplikasinya tetap berjalan mulus, cuma
menampilkan data milik orang lain. Tanpa tes ini, kerusakan semacam itu
baru ketahuan saat sudah dipakai orang.

Contoh kesalahan yang dijaga di sini: cukup satu pemanggilan yang lupa
menyertakan penyaring pemilik, dan seluruh riwayat semua pengguna ikut
terhitung di dashboard.
"""


def _scan(client, headers, url):
    r = client.post("/api/v1/scan/url", json={"url": url}, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


class TestPenolakanTanpaToken:
    def test_semua_endpoint_penting_menolak_tamu(self, client):
        """Tidak satu pun boleh terbuka tanpa masuk."""
        assert client.post("/api/v1/scan/url",
                           json={"url": "https://contoh.com"}).status_code == 401
        assert client.post("/api/v1/scan/email",
                           json={"email_content": "halo"}).status_code == 401
        assert client.get("/api/v1/dashboard/stats").status_code == 401
        assert client.get("/api/v1/dashboard/recent").status_code == 401


class TestIsolasiRiwayat:
    def test_statistik_hanya_menghitung_milik_sendiri(self, client, buat_akun):
        andi, budi = buat_akun(nama="Andi"), buat_akun(nama="Budi")

        for u in ["https://github.com", "https://wikipedia.org", "https://google.com"]:
            _scan(client, andi["headers"], u)
        _scan(client, budi["headers"], "https://slot-gacor-maxwin88.com")

        sa = client.get("/api/v1/dashboard/stats", headers=andi["headers"]).json()
        sb = client.get("/api/v1/dashboard/stats", headers=budi["headers"]).json()

        assert sa["total_scans"] == 3
        assert sb["total_scans"] == 1

    def test_riwayat_tidak_bocor_antar_akun(self, client, buat_akun):
        andi, budi = buat_akun(nama="Andi"), buat_akun(nama="Budi")
        _scan(client, andi["headers"], "https://rahasia-milik-andi.com")
        _scan(client, budi["headers"], "https://milik-budi.com")

        riwayat_budi = client.get("/api/v1/dashboard/recent",
                                  headers=budi["headers"]).json()["scans"]
        semua_input = " ".join(s["input_value"] for s in riwayat_budi)

        assert "rahasia-milik-andi" not in semua_input
        assert len(riwayat_budi) == 1

    def test_akun_baru_tidak_melihat_riwayat_tanpa_pemilik(self, client, buat_akun):
        """
        Riwayat lama yang dibuat sebelum ada sistem akun (user_id kosong)
        tidak boleh muncul di akun mana pun.
        """
        baru = buat_akun()
        r = client.get("/api/v1/dashboard/recent", headers=baru["headers"]).json()
        assert r["scans"] == []


class TestAksesBarisMilikOrangLain:
    def test_tidak_bisa_membaca_riwayat_orang_lain(self, client, buat_akun):
        andi, budi = buat_akun(), buat_akun()
        milik_andi = _scan(client, andi["headers"], "https://milik-andi.com")

        r = client.get(f"/api/v1/scan/{milik_andi['id']}", headers=budi["headers"])
        # 404, bukan 403: jawaban 403 memberi tahu bahwa id itu ADA
        assert r.status_code == 404

    def test_tidak_bisa_menghapus_riwayat_orang_lain(self, client, buat_akun):
        andi, budi = buat_akun(), buat_akun()
        milik_andi = _scan(client, andi["headers"], "https://milik-andi.com")

        r = client.delete(f"/api/v1/scan/{milik_andi['id']}", headers=budi["headers"])
        assert r.status_code == 404

        # Pastikan benar-benar masih ada
        tetap = client.get(f"/api/v1/scan/{milik_andi['id']}", headers=andi["headers"])
        assert tetap.status_code == 200

    def test_bisa_menghapus_riwayat_sendiri(self, client, buat_akun):
        andi = buat_akun()
        milik = _scan(client, andi["headers"], "https://milik-sendiri.com")

        assert client.delete(f"/api/v1/scan/{milik['id']}",
                             headers=andi["headers"]).status_code == 204
        assert client.get(f"/api/v1/scan/{milik['id']}",
                          headers=andi["headers"]).status_code == 404
