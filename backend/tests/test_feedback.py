"""
test_feedback.py
================
Tes mekanisme koreksi - bagian "belajar dari kesalahan".

Yang paling dijaga di sini bukan alur suksesnya, melainkan PENYALAHGUNAANNYA.
Kalau siapa pun bisa mengirim koreksi untuk riwayat orang lain, atau mengirim
koreksi yang sama berulang kali, data latih model berikutnya bisa diracuni
sampai modelnya justru jadi lebih buruk. Serangan semacam itu punya nama
sendiri di keamanan machine learning: data poisoning.
"""

import uuid


def _scan(client, headers, url="https://contoh-uji.com"):
    r = client.post("/api/v1/scan/url", json={"url": url}, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


class TestKirimKoreksi:
    def test_koreksi_tersimpan(self, client, buat_akun):
        akun = buat_akun()
        s = _scan(client, akun["headers"])

        r = client.post("/api/v1/feedback", headers=akun["headers"],
                        json={"scan_id": s["id"], "koreksi": "malicious"})
        assert r.status_code == 201
        d = r.json()
        assert d["koreksi"] == "malicious"
        assert d["scan_id"] == s["id"]

    def test_kirim_dua_kali_memperbarui_bukan_menumpuk(self, client, buat_akun):
        """
        Satu pemindaian cukup satu koreksi.

        Tanpa aturan ini, satu orang bisa mengirim ratusan koreksi untuk URL
        yang sama sehingga seolah jadi bukti terkuat saat pelatihan ulang.
        """
        akun = buat_akun()
        s = _scan(client, akun["headers"])

        client.post("/api/v1/feedback", headers=akun["headers"],
                    json={"scan_id": s["id"], "koreksi": "safe"})
        client.post("/api/v1/feedback", headers=akun["headers"],
                    json={"scan_id": s["id"], "koreksi": "malicious"})

        st = client.get("/api/v1/feedback/statistik",
                        headers=akun["headers"]).json()
        assert st["total_koreksi"] == 1, "koreksi kedua seharusnya memperbarui"

    def test_nilai_koreksi_tidak_sah_ditolak(self, client, buat_akun):
        """
        Nilai bebas akan mengotori data latih dengan label tidak seragam
        ("aman", "Aman", "AMAN"), dan itu tidak akan pernah memunculkan error.
        """
        akun = buat_akun()
        s = _scan(client, akun["headers"])
        r = client.post("/api/v1/feedback", headers=akun["headers"],
                        json={"scan_id": s["id"], "koreksi": "ngawur"})
        assert r.status_code == 422


class TestPenyalahgunaan:
    def test_tidak_bisa_mengoreksi_riwayat_orang_lain(self, client, buat_akun):
        andi, budi = buat_akun(), buat_akun()
        milik_andi = _scan(client, andi["headers"], "https://milik-andi.com")

        r = client.post("/api/v1/feedback", headers=budi["headers"],
                        json={"scan_id": milik_andi["id"], "koreksi": "safe"})
        # 404, bukan 403 - jawaban 403 memberi tahu bahwa id itu ADA
        assert r.status_code == 404

    def test_scan_id_karangan_ditolak(self, client, buat_akun):
        akun = buat_akun()
        r = client.post("/api/v1/feedback", headers=akun["headers"],
                        json={"scan_id": str(uuid.uuid4()), "koreksi": "safe"})
        assert r.status_code == 404

    def test_tanpa_token_ditolak(self, client, buat_akun):
        akun = buat_akun()
        s = _scan(client, akun["headers"])
        r = client.post("/api/v1/feedback",
                        json={"scan_id": s["id"], "koreksi": "safe"})
        assert r.status_code == 401


class TestStatistik:
    def test_statistik_hanya_menghitung_milik_sendiri(self, client, buat_akun):
        andi, budi = buat_akun(), buat_akun()

        a = _scan(client, andi["headers"], "https://a.com")
        client.post("/api/v1/feedback", headers=andi["headers"],
                    json={"scan_id": a["id"], "koreksi": "malicious"})

        st_budi = client.get("/api/v1/feedback/statistik",
                             headers=budi["headers"]).json()
        assert st_budi["total_koreksi"] == 0

    def test_membedakan_salah_alarm_dan_kecolongan(self, client, buat_akun):
        akun = buat_akun()
        # github.com dinilai aman; pengguna bilang sebenarnya berbahaya
        s = _scan(client, akun["headers"], "https://github.com")
        client.post("/api/v1/feedback", headers=akun["headers"],
                    json={"scan_id": s["id"], "koreksi": "malicious"})

        st = client.get("/api/v1/feedback/statistik",
                        headers=akun["headers"]).json()
        assert st["kecolongan"] == 1
        assert st["salah_alarm"] == 0
