"""
holdout_test.py
===============
Uji model dengan URL SUNGGUHAN yang tidak pernah ikut dilatih.

KENAPA FILE INI ADA
-------------------
Nilai akurasi dari train_test_split tidak bisa dipercaya sendirian. Kalau
data latih dan data uji sama-sama berasal dari satu dataset yang bocor,
keduanya mewarisi jalan pintas yang sama, jadi nilai ujinya ikut bagus.
Model versi pertama project ini mencetak akurasi 99,55% dengan cara itu,
padahal saat diberi github.com/torvalds/linux dia menjawab "berbahaya 99,97%".

Berkas ini memakai URL yang dikumpulkan manual, di luar dataset manapun,
termasuk kasus-kasus yang paling sering salah dinilai:

  - Situs terkenal DENGAN path      -> github.com/torvalds/linux
  - Situs sah yang masih memakai http -> bps.go.id
  - Situs pemerintah & kampus Indonesia
  - Situs judi online (masalah utama project ini)
  - Phishing yang meniru bank Indonesia

CARA PAKAI
----------
    python ml/evaluation/holdout_test.py

Jalankan SETIAP KALI selesai melatih model. Bandingkan hasilnya dengan
sebelumnya. Kalau akurasi trainingmu naik tapi angka di sini turun,
berarti modelmu makin hafal dataset, bukan makin pintar.

CATATAN: URL judi & phishing di bawah sengaja ditulis sebagai POLA yang
mewakili bentuk umumnya, bukan alamat aktif. Tujuannya menguji apakah
model mengenali ciri-cirinya. Jangan pernah membuka alamat semacam ini.
"""

import json
import os
import pickle
import sys

import pandas as pd

_current_file = os.path.abspath(__file__)
_project_root = os.path.abspath(os.path.join(_current_file, "..", "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from ml.predict import predict_url  # noqa: E402

MODELS_DIR = os.path.join(_project_root, "ml", "models")
METADATA_PATH = os.path.join(MODELS_DIR, "model_metadata.json")


# ============================================================
# KUMPULAN URL UJI
# label: 0 = seharusnya AMAN, 1 = seharusnya BERBAHAYA
# ============================================================

URL_UJI = [
    # ---------- Seharusnya AMAN: situs terkenal, domain polos ----------
    ("https://www.google.com", 0, "situs terkenal, domain polos"),
    ("https://www.wikipedia.org", 0, "situs terkenal, domain polos"),

    # ---------- Seharusnya AMAN: situs terkenal DENGAN path ----------
    # Inilah titik lemah utama model versi pertama. Dataset PhiUSIIL tidak
    # punya satu pun URL aman yang memakai path, jadi model menyimpulkan
    # semua URL berpath itu berbahaya.
    ("https://github.com/torvalds/linux", 0, "situs terkenal + path"),
    ("https://en.wikipedia.org/wiki/Phishing", 0, "situs terkenal + path"),
    ("https://stackoverflow.com/questions/11227809", 0, "situs terkenal + path + angka"),
    ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", 0, "situs terkenal + query string"),
    ("https://docs.python.org/3/library/urllib.parse.html", 0, "dokumentasi resmi + path dalam"),

    # ---------- Seharusnya AMAN: masih memakai http ----------
    # Banyak situs sah di Indonesia belum memakai https. Model tidak boleh
    # menyamakan "http" dengan "phishing".
    ("http://neverssl.com", 0, "situs sah yang memang http"),

    # ---------- Seharusnya AMAN: domain Indonesia ----------
    ("https://www.bps.go.id", 0, "situs pemerintah"),
    ("https://www.kemdikbud.go.id", 0, "situs pemerintah"),
    ("https://www.ui.ac.id/akademik", 0, "situs kampus + path"),
    ("https://www.polban.ac.id", 0, "situs kampus"),
    ("https://www.bri.co.id", 0, "situs bank resmi"),
    ("https://www.tokopedia.com/search?q=laptop", 0, "e-commerce + query"),

    # ---------- Seharusnya BERBAHAYA: judi online ----------
    # Ini masalah utama yang mau diselesaikan project ini. Perhatikan:
    # dataset PhiUSIIL TIDAK punya kategori judi sama sekali, jadi kalau
    # model menjawab benar di sini, kemungkinan besar itu kebetulan
    # (karena ada path atau TLD murah), bukan karena paham ciri judi.
    ("https://slot-gacor-maxwin88.com/daftar", 1, "judi online"),
    ("https://situsjudibola-terpercaya.xyz", 1, "judi online, domain polos"),
    ("https://gacor777-login.top/", 1, "judi online"),
    ("https://rtp-slot-zeus.online/deposit", 1, "judi online"),
    ("https://depo25-bonus25.site", 1, "judi online, domain polos"),

    # ---------- Seharusnya BERBAHAYA: phishing bank Indonesia ----------
    ("https://bri-mobile-verifikasi.com/login", 1, "phishing bank"),
    ("https://klikbca-secure-login.net/auth", 1, "phishing bank"),
    ("http://mandiri-online.verify-akun.tk/masuk", 1, "phishing bank, TLD gratis"),

    # ---------- Seharusnya BERBAHAYA: phishing umum ----------
    ("http://192.168.1.1/bank/verify.html", 1, "alamat IP mentah"),
    ("https://accounts.google.com.verify-account.xyz/signin", 1, "domain menyamar"),
    ("http://paypal-secure-update.ml/webscr?cmd=login", 1, "menyamar merek + TLD gratis"),
    ("https://appleid-locked-verify.ga/unlock", 1, "menyamar merek + TLD gratis"),
]


def main():
    if not os.path.exists(METADATA_PATH):
        print(f"ERROR: {METADATA_PATH} tidak ditemukan.")
        print("Latih model dulu: python ml/models/train_model.py")
        sys.exit(1)

    print("=" * 88)
    print("UJI HOLDOUT - URL SUNGGUHAN DI LUAR DATASET")
    print("Diuji lewat ml/predict.py, yaitu mesin yang SAMA persis dipakai")
    print("aplikasi (daftar putih + aturan + model), bukan model mentah.")
    print("=" * 88)

    baris = []
    for url, harusnya, catatan in URL_UJI:
        hasil = predict_url(url)
        # "Mencurigakan" dihitung sebagai terdeteksi: bagi pengguna, peringatan
        # sudah cukup untuk membuatnya berhenti dan berpikir dua kali.
        tebakan = 1 if hasil["threat_label"] in ("Malicious", "Suspicious") else 0
        baris.append(
            {"url": url, "harusnya": harusnya, "tebakan": tebakan,
             "skor": hasil["risk_score"], "catatan": catatan,
             "benar": tebakan == harusnya}
        )

    df = pd.DataFrame(baris)

    # ---------- Tabel hasil ----------
    for kelompok, judul in ((0, "SEHARUSNYA AMAN"), (1, "SEHARUSNYA BERBAHAYA")):
        bagian = df[df.harusnya == kelompok]
        print(f"\n{judul}")
        print("-" * 88)
        for _, r in bagian.iterrows():
            tanda = "OK  " if r.benar else "SALAH"
            url_pendek = r.url if len(r.url) <= 46 else r.url[:43] + "..."
            print(f"  [{tanda}] {url_pendek:<46} {r.skor*100:6.2f}%  {r.catatan}")

    # ---------- Ringkasan ----------
    aman = df[df.harusnya == 0]
    bahaya = df[df.harusnya == 1]

    akurasi = df.benar.mean()
    salah_alarm = int((~aman.benar).sum())     # aman divonis berbahaya
    lolos = int((~bahaya.benar).sum())         # berbahaya divonis aman

    print("\n" + "=" * 88)
    print("RINGKASAN")
    print("=" * 88)
    print(f"  Akurasi keseluruhan       : {akurasi*100:.1f}%  ({int(df.benar.sum())}/{len(df)})")
    print(f"  Situs aman divonis bahaya : {salah_alarm}/{len(aman)}  <- salah alarm")
    print(f"  Ancaman lolos terdeteksi  : {lolos}/{len(bahaya)}")

    print("\n  Cara membaca:")
    print("    Salah alarm tinggi = model terlalu galak, situs biasa ikut diblokir.")
    print("    Ancaman lolos tinggi = model terlalu longgar, ancaman asli lewat.")
    print("    Keduanya harus rendah. Akurasi dataset yang tinggi TIDAK menjamin ini.")

    if salah_alarm > len(aman) * 0.3:
        print("\n  [PERINGATAN] Terlalu banyak situs sah divonis berbahaya.")
        print("  Ini gejala khas dataset bocor: model belajar 'ada path' atau")
        print("  'memakai http' berarti phishing. Jalankan pemeriksaan dataset:")
        print("      python ml/data/check_leakage.py")

    print()
    return 0 if akurasi >= 0.8 else 1


if __name__ == "__main__":
    sys.exit(main())
