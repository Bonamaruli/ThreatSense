"""
test_auth.py
============
Tes pendaftaran, masuk, dan pengelolaan profil.

Tes yang paling penting di berkas ini adalah yang menguji KEGAGALAN:
sandi salah harus ditolak, email kembar harus ditolak, token palsu harus
ditolak. Fitur yang berhasil biasanya ketahuan rusak saat dipakai; lubang
keamanan tidak - dia diam saja sampai ada yang memanfaatkannya.
"""


class TestPendaftaran:
    def test_daftar_berhasil_dan_langsung_dapat_token(self, client):
        r = client.post("/api/v1/auth/register", json={
            "nama": "Bona Panjaitan",
            "email": "bona@contoh.com",
            "sandi": "sandiRahasia1",
        })
        assert r.status_code == 201
        d = r.json()
        assert d["access_token"]
        assert d["user"]["nama"] == "Bona Panjaitan"
        assert d["user"]["email"] == "bona@contoh.com"

    def test_hash_sandi_tidak_pernah_ikut_terkirim(self, client):
        """Kebocoran paling fatal: hash sandi ikut terkirim ke browser."""
        r = client.post("/api/v1/auth/register", json={
            "nama": "Rahasia", "email": "rahasia@contoh.com", "sandi": "sandiRahasia1",
        })
        assert "hash_sandi" not in r.text
        assert "sandiRahasia1" not in r.text

    def test_email_kembar_ditolak(self, client):
        data = {"nama": "Kembar", "email": "kembar@contoh.com", "sandi": "sandiRahasia1"}
        assert client.post("/api/v1/auth/register", json=data).status_code == 201
        assert client.post("/api/v1/auth/register", json=data).status_code == 409

    def test_email_disimpan_huruf_kecil(self, client):
        """HURUF@BESAR.com dan huruf@besar.com harus dianggap akun yang sama."""
        client.post("/api/v1/auth/register", json={
            "nama": "Besar", "email": "BESAR@Contoh.COM", "sandi": "sandiRahasia1",
        })
        r = client.post("/api/v1/auth/login", json={
            "email": "besar@contoh.com", "sandi": "sandiRahasia1",
        })
        assert r.status_code == 200

    def test_sandi_terlalu_pendek_ditolak(self, client):
        r = client.post("/api/v1/auth/register", json={
            "nama": "Pendek", "email": "pendek@contoh.com", "sandi": "1234567",
        })
        assert r.status_code == 422

    def test_email_tidak_valid_ditolak(self, client):
        r = client.post("/api/v1/auth/register", json={
            "nama": "Salah", "email": "bukan-email", "sandi": "sandiRahasia1",
        })
        assert r.status_code == 422


class TestMasuk:
    def test_sandi_salah_ditolak(self, client, buat_akun):
        akun = buat_akun()
        r = client.post("/api/v1/auth/login", json={
            "email": akun["email"], "sandi": "salahTotal123",
        })
        assert r.status_code == 401

    def test_email_tidak_ada_ditolak(self, client):
        r = client.post("/api/v1/auth/login", json={
            "email": "tidakada@contoh.com", "sandi": "apapun123",
        })
        assert r.status_code == 401

    def test_pesan_sama_untuk_email_salah_dan_sandi_salah(self, client, buat_akun):
        """
        Kalau pesannya berbeda, halaman masuk bisa dipakai untuk memeriksa
        email mana yang punya akun di sistem ini.
        """
        akun = buat_akun()
        a = client.post("/api/v1/auth/login", json={
            "email": akun["email"], "sandi": "salahTotal123"}).json()
        b = client.post("/api/v1/auth/login", json={
            "email": "tidakada@contoh.com", "sandi": "salahTotal123"}).json()
        assert a["detail"] == b["detail"]


class TestToken:
    def test_tanpa_token_ditolak(self, client):
        assert client.get("/api/v1/auth/me").status_code == 401

    def test_token_ngawur_ditolak(self, client):
        r = client.get("/api/v1/auth/me",
                       headers={"Authorization": "Bearer ngawur.sekali.ini"})
        assert r.status_code == 401

    def test_token_sah_mengembalikan_profil(self, client, buat_akun):
        akun = buat_akun(nama="Siti Rahayu")
        r = client.get("/api/v1/auth/me", headers=akun["headers"])
        assert r.status_code == 200
        assert r.json()["nama"] == "Siti Rahayu"


class TestUbahProfil:
    def test_ubah_nama(self, client, buat_akun):
        akun = buat_akun()
        r = client.put("/api/v1/auth/me", json={"nama": "Nama Baru"},
                       headers=akun["headers"])
        assert r.status_code == 200
        assert r.json()["nama"] == "Nama Baru"

    def test_email_bentrok_ditolak(self, client, buat_akun):
        a, b = buat_akun(), buat_akun()
        r = client.put("/api/v1/auth/me", json={"email": b["email"]},
                       headers=a["headers"])
        assert r.status_code == 409


class TestGantiSandi:
    def test_sandi_lama_salah_ditolak(self, client, buat_akun):
        akun = buat_akun()
        r = client.put("/api/v1/auth/me/password", headers=akun["headers"], json={
            "sandi_lama": "salahTotal123", "sandi_baru": "sandiBaruSekali1",
        })
        assert r.status_code == 400

    def test_sandi_baru_sama_dengan_lama_ditolak(self, client, buat_akun):
        akun = buat_akun()
        r = client.put("/api/v1/auth/me/password", headers=akun["headers"], json={
            "sandi_lama": akun["sandi"], "sandi_baru": akun["sandi"],
        })
        assert r.status_code == 400

    def test_ganti_sandi_berhasil_lalu_sandi_lama_tidak_berlaku(self, client, buat_akun):
        akun = buat_akun()
        r = client.put("/api/v1/auth/me/password", headers=akun["headers"], json={
            "sandi_lama": akun["sandi"], "sandi_baru": "sandiBaruSekali1",
        })
        assert r.status_code == 204

        gagal = client.post("/api/v1/auth/login", json={
            "email": akun["email"], "sandi": akun["sandi"]})
        assert gagal.status_code == 401

        berhasil = client.post("/api/v1/auth/login", json={
            "email": akun["email"], "sandi": "sandiBaruSekali1"})
        assert berhasil.status_code == 200
