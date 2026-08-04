"""
email_test.py
=============
Uji mesin deteksi email dengan contoh yang ditulis manual.

KENAPA CONTOHNYA DITULIS SENDIRI
--------------------------------
Belum ada kumpulan email phishing berbahasa Indonesia yang tersedia umum
dan sudah diberi label. Jadi contoh di sini disusun manual berdasarkan pola
yang benar-benar beredar: pemberitahuan palsu dari bank, tagihan palsu,
undian bohongan.

Karena contohnya sedikit dan ditulis oleh orang yang sama yang membuat
aturannya, angka di sini TIDAK BOLEH dipakai sebagai klaim akurasi di
laporan. Gunanya adalah menjaga agar perubahan aturan di kemudian hari
tidak diam-diam merusak yang sudah benar.

Yang paling penting diperhatikan justru bagian EMAIL SAH: kalau email biasa
mulai divonis berbahaya, aturannya sudah terlalu galak.

CARA PAKAI
----------
    python ml/evaluation/email_test.py
"""

import os
import sys

_current = os.path.abspath(__file__)
_root = os.path.abspath(os.path.join(_current, "..", "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from ml.predict_email import predict_email  # noqa: E402


# ============================================================
# CONTOH EMAIL  (label: 0 = sah, 1 = phishing)
# ============================================================

CONTOH = [
    # ---------------- PHISHING ----------------
    ("Bank palsu dari Gmail + tautan menipu", 1, """From: "Bank BRI" <bri.verifikasi2024@gmail.com>
Reply-To: penampung.data@mail.ru
Subject: SEGERA - Rekening Anda Akan Diblokir Dalam 24 Jam

Nasabah yang terhormat,
Kami mendeteksi aktivitas mencurigakan. Segera verifikasi kata sandi dan
PIN Anda melalui tautan berikut:
<a href="http://bri-verifikasi-nasabah.tk/login">https://bri.co.id/verifikasi</a>
Jangan abaikan pesan ini.
"""),

    ("Undian palsu", 1, """From: "Undian Shopee" <shopee.hadiah@yahoo.com>
Subject: Selamat Anda Terpilih Sebagai Pemenang!

Selamat anda terpilih sebagai pemenang undian bulanan!
Hadiah senilai Rp 25.000.000 menanti. Klaim sekarang juga sebelum
kedaluwarsa: http://shopee-undian-resmi.xyz/klaim
"""),

    ("Lampiran ekstensi ganda", 1, """From: "Finance Dept" <billing@invoice-center.top>
Subject: Invoice Pembayaran Tertunggak

Terlampir invoice yang belum dibayar. Mohon segera diproses.

Content-Type: application/octet-stream; name="invoice_2024.pdf.exe"
Content-Disposition: attachment; filename="invoice_2024.pdf.exe"
"""),

    ("Phishing pajak", 1, """From: "Ditjen Pajak" <pajak.restitusi@gmail.com>
Subject: PENTING - Restitusi Pajak Anda Menunggu Konfirmasi

Wajib pajak yang terhormat, restitusi Anda siap dicairkan.
Konfirmasi nomor rekening dan NIK Anda segera melalui:
http://djp-restitusi-online.click/konfirmasi
Batas waktu 2x24 jam.
"""),

    ("Email berisi tautan judi", 1, """From: promo@newsletter-harian.com
Subject: Bonus New Member Hari Ini

Dapatkan bonus dan cuan setiap hari, daftar sekarang:
https://slot-gacor-maxwin88.com/daftar
"""),

    # ---------------- SAH ----------------
    ("Notifikasi GitHub", 0, """From: GitHub <noreply@github.com>
Subject: [torvalds/linux] New pull request opened

A new pull request was opened in torvalds/linux.
View it here: https://github.com/torvalds/linux/pull/1234
You are receiving this because you are watching this repository.
"""),

    ("Email kampus", 0, """From: "Akademik Polban" <akademik@polban.ac.id>
Subject: Pengumuman Jadwal Ujian Akhir Semester

Kepada seluruh mahasiswa,
Jadwal ujian akhir semester telah terbit dan dapat dilihat pada
https://www.polban.ac.id/akademik/jadwal
Harap hadir 15 menit sebelum ujian dimulai.
"""),

    ("Struk belanja resmi", 0, """From: Tokopedia <noreply@tokopedia.com>
Subject: Pesanan Anda Telah Dikirim

Halo, pesanan kamu sudah dikirim dan sedang dalam perjalanan.
Lacak di https://www.tokopedia.com/order/12345
Terima kasih sudah berbelanja.
"""),

    ("Email pribadi biasa", 0, """From: Budi Santoso <budi.santoso@gmail.com>
Subject: Materi rapat besok

Hai, ini materi untuk rapat besok ya. Tolong dibaca dulu.
Kalau ada yang kurang jelas kabari saja.
Terima kasih.
"""),

    ("Newsletter teknologi", 0, """From: Dev Weekly <hello@devweekly.io>
Subject: Edisi 42 - Rilis Python 3.13

Halo,
Minggu ini: rilis Python 3.13, tips optimasi database, dan wawancara
dengan maintainer open source.
Baca selengkapnya: https://devweekly.io/issues/42
Berhenti berlangganan kapan saja.
"""),

    # Email sah yang MEMANG mendesak - jangan sampai kena hanya karena ini
    ("Peringatan sah yang mendesak", 0, """From: "Tim IT Polban" <it-support@polban.ac.id>
Subject: Pemeliharaan Server Malam Ini

Rekan-rekan,
Server akan dimatikan sementara malam ini pukul 23.00 untuk pemeliharaan.
Mohon segera simpan pekerjaan Anda sebelum waktu tersebut.
Informasi lengkap: https://www.polban.ac.id/pengumuman
"""),
]


def main():
    print("=" * 84)
    print("UJI MESIN DETEKSI EMAIL")
    print("=" * 84)

    benar = salah_alarm = lolos = n_sah = n_phish = 0
    baris = []

    for nama, harus, isi in CONTOH:
        h = predict_email(isi)
        tebak = 1 if h["threat_label"] in ("Malicious", "Suspicious") else 0
        ok = tebak == harus
        benar += ok

        if harus == 0:
            n_sah += 1
            if not ok:
                salah_alarm += 1
        else:
            n_phish += 1
            if not ok:
                lolos += 1

        baris.append((ok, nama, harus, h))

    for kelompok, judul in ((1, "SEHARUSNYA PHISHING"), (0, "SEHARUSNYA SAH")):
        print(f"\n{judul}")
        print("-" * 84)
        for ok, nama, harus, h in baris:
            if harus != kelompok:
                continue
            tanda = "OK   " if ok else "SALAH"
            alasan = h["explanations"][0]["judul"] if h["explanations"] else "-"
            print(f"  [{tanda}] {h['risk_score']*100:5.0f}%  {nama:<38} {alasan[:28]}")

    print("\n" + "=" * 84)
    print("RINGKASAN")
    print("=" * 84)
    print(f"  Benar               : {benar}/{len(CONTOH)}")
    print(f"  Email sah salah vonis: {salah_alarm}/{n_sah}   <- paling penting dijaga rendah")
    print(f"  Phishing lolos       : {lolos}/{n_phish}")
    print("\n  Catatan: contoh ditulis manual dan jumlahnya sedikit, jadi angka")
    print("  ini TIDAK boleh dipakai sebagai klaim akurasi di laporan.")
    print()

    return 0 if salah_alarm == 0 and lolos == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
