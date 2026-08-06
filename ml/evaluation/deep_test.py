"""
deep_test.py
============
Membandingkan pemindaian CEPAT (nama domain saja) dengan pemindaian
MENDALAM (benar-benar membuka alamatnya), memakai URL sungguhan.

Pertanyaan yang dijawab berkas ini: apakah tambahan waktu 3-8 detik itu
benar-benar terbayar dengan kesimpulan yang lebih baik?

Perhatikan terutama dua kolom terakhir. Kalau pemindaian mendalam tidak
memperbaiki apa pun, kelambatannya tidak ada gunanya dan sebaiknya jujur
diakui - bukan dipertahankan supaya terlihat canggih.

CARA PAKAI
    python ml/evaluation/deep_test.py
"""

import os
import sys
import time
import warnings

warnings.filterwarnings("ignore")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from ml.scoring.url import predict_url  # noqa: E402

# label: 0 = seharusnya aman, 1 = seharusnya berbahaya
URL_UJI = [
    ("https://github.com", 0, "situs terkenal"),
    ("https://www.wikipedia.org", 0, "situs terkenal"),
    ("https://tokopedia.com", 0, "e-commerce Indonesia"),
    ("https://www.bri.co.id", 0, "bank resmi"),
    ("https://stackoverflow.com/questions/11227809", 0, "situs terkenal + path"),
    ("https://slot-gacor-maxwin88.com/daftar", 1, "judi online"),
    ("https://bri-mobile-verifikasi.com/login", 1, "phishing bank"),
    ("http://192.168.1.1/bank/verify.html", 1, "alamat IP mentah"),
    ("http://paypal-secure-update.ml/webscr?cmd=login", 1, "meniru merek"),
]


def main():
    print("=" * 96)
    print("PERBANDINGAN: PEMINDAIAN CEPAT vs MENDALAM")
    print("=" * 96)
    print(f"{'URL':<44} {'CEPAT':<20} {'MENDALAM':<20} {'HARUS'}")
    print("-" * 96)

    benar_cepat = benar_dalam = 0
    waktu_cepat = waktu_dalam = 0.0

    for url, harus, catatan in URL_UJI:
        t = time.time()
        a = predict_url(url)
        waktu_cepat += time.time() - t

        t = time.time()
        b = predict_url(url, mendalam=True)
        waktu_dalam += time.time() - t

        ta = 1 if a["threat_label"] in ("Malicious", "Suspicious") else 0
        tb = 1 if b["threat_label"] in ("Malicious", "Suspicious") else 0
        benar_cepat += ta == harus
        benar_dalam += tb == harus

        ca = "OK " if ta == harus else "SALAH"
        cb = "OK " if tb == harus else "SALAH"
        print(f"{url[:42]:<44} "
              f"{a['threat_label'][:9]:<9}{a['risk_score']*100:>4.0f}% {ca:<5} "
              f"{b['threat_label'][:9]:<9}{b['risk_score']*100:>4.0f}% {cb:<5} "
              f"{'BAHAYA' if harus else 'AMAN'}")

    n = len(URL_UJI)
    print("-" * 96)
    print(f"\n{'':22s}{'CEPAT':>14}{'MENDALAM':>14}")
    print(f"{'Benar':22s}{benar_cepat:>10}/{n:<3}{benar_dalam:>10}/{n:<3}")
    print(f"{'Akurasi':22s}{benar_cepat/n*100:>13.1f}%{benar_dalam/n*100:>13.1f}%")
    print(f"{'Waktu rata-rata':22s}{waktu_cepat/n:>12.2f}s{waktu_dalam/n:>13.2f}s")

    selisih = benar_dalam - benar_cepat
    print()
    if selisih > 0:
        print(f"Pemindaian mendalam benar {selisih} kasus lebih banyak.")
        print("Tambahan waktunya terbayar.")
    elif selisih == 0:
        print("Keduanya sama benar pada kumpulan uji ini.")
        print("Nilai lebih pemindaian mendalam ada pada BUKTI yang ditampilkan")
        print("(umur domain, negara, isi halaman) - bukan pada angka akurasinya.")
    else:
        print(f"Pemindaian mendalam justru salah {-selisih} kasus lebih banyak.")
        print("Periksa kembali bobot aturan bukti di ml/deep_rules.py.")


if __name__ == "__main__":
    main()
