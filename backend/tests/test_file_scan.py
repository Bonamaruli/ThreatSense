"""
test_file_scan.py
=================
Tes File Scanner - analisis statis isi berkas.

Berkas uji dibuat langsung di dalam tes, bukan diambil dari koleksi malware
sungguhan. Menyimpan malware asli di repositori tugas akhir adalah risiko
yang tidak sepadan, dan pola yang diuji di sini (penyamaran ekstensi, makro,
program di dalam arsip) bisa ditiru dengan aman memakai berkas buatan.

Yang dijaga: berkas TIDAK PERNAH dijalankan, hanya dibaca sebagai data.
"""

import io
import zipfile

import pytest

PDF_BERSIH = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n%%EOF"
PNG_BERSIH = b"\x89PNG\r\n\x1a\n" + b"\x00" * 300
PROGRAM_WINDOWS = b"MZ\x90\x00\x03" + b"\x00" * 400


def _zip(isi: list[str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for n in isi:
            z.writestr(n, b"isi contoh")
    return buf.getvalue()


def _unggah(client, headers, nama, data, tipe="application/pdf"):
    return client.post(
        "/api/v1/scan/file",
        files={"file": (nama, data, tipe)},
        headers=headers,
    )


class TestBerkasBersih:
    def test_pdf_biasa_dinilai_aman(self, client, buat_akun):
        akun = buat_akun()
        r = _unggah(client, akun["headers"], "laporan.pdf", PDF_BERSIH)
        assert r.status_code == 200
        assert r.json()["threat_label"] == "Safe"

    def test_gambar_dinilai_aman(self, client, buat_akun):
        """Gambar wajar punya entropi tinggi - tidak boleh dituduh karena itu."""
        akun = buat_akun()
        r = _unggah(client, akun["headers"], "foto.png", PNG_BERSIH, "image/png")
        assert r.json()["threat_label"] == "Safe"


class TestPenyamaran:
    def test_program_menyamar_jadi_pdf_tertangkap(self, client, buat_akun):
        """
        Kasus terpenting: berkas bernama .pdf yang isinya program Windows.

        Versi lama hanya membaca NAMA berkas, jadi penyamaran seperti ini
        lolos begitu saja - justru trik yang paling sering dipakai.
        """
        akun = buat_akun()
        r = _unggah(client, akun["headers"], "faktur.pdf", PROGRAM_WINDOWS)
        assert r.status_code == 200
        d = r.json()
        assert d["threat_label"] == "Malicious"
        assert d["risk_score"] >= 0.9

        judul = " ".join(e["judul"] for e in d["explanations"])
        assert "program" in judul.lower()

    def test_ekstensi_ganda_tertangkap(self, client, buat_akun):
        akun = buat_akun()
        r = _unggah(client, akun["headers"], "invoice.pdf.exe", PROGRAM_WINDOWS)
        d = r.json()
        assert d["threat_label"] == "Malicious"
        judul = " ".join(e["judul"] for e in d["explanations"]).lower()
        assert "ganda" in judul


class TestIsiBerbahaya:
    def test_dokumen_bermakro_tertangkap(self, client, buat_akun):
        akun = buat_akun()
        docm = _zip(["word/document.xml", "word/vbaProject.bin"])
        r = _unggah(client, akun["headers"], "surat.docm", docm,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        d = r.json()
        assert d["threat_label"] == "Malicious"
        assert "makro" in " ".join(e["judul"] for e in d["explanations"]).lower()

    def test_program_di_dalam_arsip_tertangkap(self, client, buat_akun):
        akun = buat_akun()
        z = _zip(["readme.txt", "setup.exe"])
        r = _unggah(client, akun["headers"], "kiriman.docx", z,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        d = r.json()
        assert d["threat_label"] in ("Malicious", "Suspicious")

    def test_pdf_dengan_javascript_otomatis_tertangkap(self, client, buat_akun):
        akun = buat_akun()
        jahat = b"%PDF-1.4\n/OpenAction << /S /JavaScript /JS (app.alert) >>\n%%EOF"
        r = _unggah(client, akun["headers"], "undangan.pdf", jahat)
        d = r.json()
        assert d["threat_label"] == "Malicious"


class TestBuktiDanBatasan:
    def test_hasil_menyertakan_bukti(self, client, buat_akun):
        akun = buat_akun()
        r = _unggah(client, akun["headers"], "laporan.pdf", PDF_BERSIH)
        d = r.json()
        label = [b["label"] for b in (d.get("evidence_summary") or [])]
        assert "SHA-256" in label
        assert "Jenis sebenarnya" in label

    def test_hasil_selalu_menyertakan_alasan(self, client, buat_akun):
        akun = buat_akun()
        d = _unggah(client, akun["headers"], "laporan.pdf", PDF_BERSIH).json()
        assert d["explanations"]
        assert d["explanations"][0]["alasan"]

    def test_tipe_tidak_diizinkan_ditolak(self, client, buat_akun):
        akun = buat_akun()
        r = _unggah(client, akun["headers"], "jahat.exe", PROGRAM_WINDOWS,
                    "application/x-msdownload")
        assert r.status_code == 415

    def test_tanpa_token_ditolak(self, client):
        r = client.post("/api/v1/scan/file",
                        files={"file": ("a.pdf", PDF_BERSIH, "application/pdf")})
        assert r.status_code == 401
