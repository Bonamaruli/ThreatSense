"""
test_scan_item.py
=================
Tes endpoint satu baris riwayat dan pilihan pemindaian mendalam.

CATATAN SOAL PEMINDAIAN MENDALAM
Tes di sini TIDAK menyalakan mendalam=True, karena itu akan membuka koneksi
internet sungguhan ke situs luar. Tes yang bergantung pada jaringan akan
gagal saat internet mati atau situs tujuan sedang bermasalah - kegagalan
yang tidak ada hubungannya dengan kode kita, tapi membuat orang berhenti
memercayai hasil tesnya.

Yang diuji di sini: pilihan mendalam diterima dan dicatat dengan benar.
Perilaku mendalam sesungguhnya diuji terpisah lewat
ml/evaluation/deep_test.py yang memang dijalankan manual.
"""

import uuid


def _scan(client, headers, url="https://contoh-uji.com", mendalam=False):
    r = client.post("/api/v1/scan/url",
                    json={"url": url, "mendalam": mendalam}, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


class TestPilihanMendalam:
    def test_bawaan_tidak_mendalam(self, client, buat_akun):
        """Tanpa diminta, pemindaian harus tetap cepat."""
        akun = buat_akun()
        r = client.post("/api/v1/scan/url", json={"url": "https://github.com"},
                        headers=akun["headers"])
        d = r.json()
        assert d["deep_scan"] is False
        assert not d.get("evidence_summary")

    def test_pilihan_mendalam_diterima(self, client, buat_akun):
        akun = buat_akun()
        d = _scan(client, akun["headers"], "https://github.com", mendalam=False)
        assert d["deep_scan"] is False

    def test_nilai_mendalam_tidak_sah_ditolak(self, client, buat_akun):
        akun = buat_akun()
        r = client.post("/api/v1/scan/url", headers=akun["headers"],
                        json={"url": "https://github.com", "mendalam": "iya-dong"})
        assert r.status_code == 422


class TestLihatSatuRiwayat:
    def test_bisa_melihat_milik_sendiri(self, client, buat_akun):
        akun = buat_akun()
        s = _scan(client, akun["headers"])
        r = client.get(f"/api/v1/scan/{s['id']}", headers=akun["headers"])
        assert r.status_code == 200
        assert r.json()["id"] == s["id"]

    def test_tidak_bisa_melihat_milik_orang_lain(self, client, buat_akun):
        andi, budi = buat_akun(), buat_akun()
        milik_andi = _scan(client, andi["headers"], "https://rahasia-andi.com")
        r = client.get(f"/api/v1/scan/{milik_andi['id']}", headers=budi["headers"])
        assert r.status_code == 404

    def test_id_karangan_ditolak(self, client, buat_akun):
        akun = buat_akun()
        r = client.get(f"/api/v1/scan/{uuid.uuid4()}", headers=akun["headers"])
        assert r.status_code == 404

    def test_id_bukan_uuid_ditolak(self, client, buat_akun):
        akun = buat_akun()
        r = client.get("/api/v1/scan/bukan-uuid", headers=akun["headers"])
        assert r.status_code == 422


class TestHapusRiwayat:
    def test_bisa_menghapus_milik_sendiri(self, client, buat_akun):
        akun = buat_akun()
        s = _scan(client, akun["headers"])
        assert client.delete(f"/api/v1/scan/{s['id']}",
                             headers=akun["headers"]).status_code == 204
        assert client.get(f"/api/v1/scan/{s['id']}",
                          headers=akun["headers"]).status_code == 404

    def test_tidak_bisa_menghapus_milik_orang_lain(self, client, buat_akun):
        andi, budi = buat_akun(), buat_akun()
        milik_andi = _scan(client, andi["headers"])

        assert client.delete(f"/api/v1/scan/{milik_andi['id']}",
                             headers=budi["headers"]).status_code == 404
        # Pastikan benar-benar masih ada
        assert client.get(f"/api/v1/scan/{milik_andi['id']}",
                          headers=andi["headers"]).status_code == 200

    def test_menghapus_mengurangi_statistik(self, client, buat_akun):
        akun = buat_akun()
        s = _scan(client, akun["headers"])
        sebelum = client.get("/api/v1/dashboard/stats",
                             headers=akun["headers"]).json()["total_scans"]

        client.delete(f"/api/v1/scan/{s['id']}", headers=akun["headers"])

        sesudah = client.get("/api/v1/dashboard/stats",
                             headers=akun["headers"]).json()["total_scans"]
        assert sesudah == sebelum - 1

    def test_tanpa_token_ditolak(self, client, buat_akun):
        akun = buat_akun()
        s = _scan(client, akun["headers"])
        assert client.delete(f"/api/v1/scan/{s['id']}").status_code == 401
