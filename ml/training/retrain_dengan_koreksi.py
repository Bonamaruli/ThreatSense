"""
retrain_dengan_koreksi.py
=========================
Melatih ulang model dengan menambahkan koreksi pengguna sebagai data latih.

INILAH BAGIAN "BELAJAR DARI KESALAHAN"
--------------------------------------
Model biasa berhenti pandai di titik saat ia dilatih. Skrip ini menutup
lingkarannya:

    pengguna memindai  ->  sistem menilai  ->  pengguna mengoreksi kalau
    salah  ->  koreksi disimpan  ->  model dilatih ulang termasuk koreksi
    itu  ->  kesalahan yang sama tidak terulang

Yang membuatnya berharga: koreksi datang dari kasus NYATA yang membuat
sistem meleset. Satu contoh sulit yang benar-benar salah dinilai jauh lebih
berguna untuk belajar daripada seribu contoh mudah yang sudah pasti benar.

BOBOT KOREKSI DILEBIHKAN
------------------------
Koreksi jumlahnya sedikit dibanding 40.000 baris data latih utama. Kalau
diperlakukan sama, pengaruhnya tenggelam dan model tidak berubah apa pun.
Karena itu tiap koreksi diberi bobot lebih besar - lihat BOBOT_KOREKSI.

CARA PAKAI
----------
    python ml/models/retrain_dengan_koreksi.py            # lihat dulu
    python ml/models/retrain_dengan_koreksi.py --latih    # benar-benar latih
"""

import argparse
import json
import os
import sys

import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
_BACKEND = os.path.join(_ROOT, "backend")
for p in (_ROOT, _BACKEND):
    if p not in sys.path:
        sys.path.insert(0, p)

DATASET = os.path.join(_ROOT, "ml", "data", "processed", "dataset_features.csv")

# Satu koreksi dihitung sebanyak ini saat pelatihan.
#
# Kenapa perlu: 40.000 baris data latih vs (misalnya) 20 koreksi. Tanpa
# pembobotan, 20 baris itu tidak akan mengubah apa pun. Angka 50 dipilih
# supaya koreksi terasa pengaruhnya tapi tidak sampai menguasai model -
# kalau terlalu besar, model malah jadi hafal segelintir kasus dan lupa
# pola umumnya.
BOBOT_KOREKSI = 50

# Di bawah jumlah ini, pelatihan ulang belum ada gunanya. Terlalu sedikit
# contoh justru berisiko menggeser model ke arah yang salah.
MINIMAL_KOREKSI = 10


def ambil_koreksi() -> pd.DataFrame:
    """Baca koreksi pengguna beserta fitur URL saat dipindai dulu."""
    from sqlalchemy import text
    from app.database import engine

    q = text("""
        SELECT s.input_value, s.features_json, s.risk_score,
               s.threat_label, f.user_correction
        FROM scan_feedback f
        JOIN scan_history s ON s.id = f.scan_id
        WHERE s.scan_type = 'url'
          AND s.features_json IS NOT NULL
          AND f.user_correction IS NOT NULL
    """)
    with engine.connect() as cx:
        baris = [dict(r._mapping) for r in cx.execute(q)]

    if not baris:
        return pd.DataFrame()

    data = []
    for b in baris:
        fitur = b["features_json"]
        if isinstance(fitur, str):
            fitur = json.loads(fitur)
        if not isinstance(fitur, dict):
            continue

        # 'suspicious' sengaja DIBUANG, bukan dipaksa jadi salah satu sisi.
        #
        # Model ini menjawab dua kemungkinan: aman atau berbahaya. Memaksa
        # "mencurigakan" masuk ke salah satunya berarti mengajarkan sesuatu
        # yang pengguna sendiri tidak yakin - itu menambah derau, bukan
        # pengetahuan.
        if b["user_correction"] == "safe":
            label = 0
        elif b["user_correction"] == "malicious":
            label = 1
        else:
            continue

        fitur["is_phishing"] = label
        fitur["url"] = b["input_value"]
        data.append(fitur)

    return pd.DataFrame(data)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--latih", action="store_true",
                   help="Benar-benar latih ulang (tanpa ini cuma melihat)")
    args = p.parse_args()

    print("=" * 70)
    print("PELATIHAN ULANG DENGAN KOREKSI PENGGUNA")
    print("=" * 70)

    koreksi = ambil_koreksi()
    if koreksi.empty:
        print("\nBelum ada koreksi yang bisa dipakai.")
        print("Koreksi terkumpul saat pengguna menekan tombol 'sebenarnya")
        print("aman' atau 'sebenarnya berbahaya' di hasil pemindaian.")
        return

    n_aman = int((koreksi["is_phishing"] == 0).sum())
    n_bahaya = int((koreksi["is_phishing"] == 1).sum())
    print(f"\nKoreksi terkumpul : {len(koreksi)}")
    print(f"  sebenarnya aman     : {n_aman}")
    print(f"  sebenarnya berbahaya: {n_bahaya}")

    if len(koreksi) < MINIMAL_KOREKSI:
        print(f"\nBelum cukup. Perlu minimal {MINIMAL_KOREKSI} koreksi supaya")
        print("pelatihan ulang bermakna - terlalu sedikit contoh justru")
        print("berisiko menggeser model ke arah yang keliru.")
        return

    if not os.path.exists(DATASET):
        print(f"\nDataset utama tidak ada di {DATASET}")
        print("Jalankan dulu: python ml/data/build_dataset.py")
        sys.exit(1)

    dasar = pd.read_csv(DATASET)
    print(f"Dataset utama     : {len(dasar):,} baris")

    # Samakan kolomnya - koreksi lama bisa saja punya set fitur berbeda
    # kalau ekstraktor fiturnya pernah diubah sejak pemindaian itu.
    kolom = [c for c in dasar.columns if c not in ("is_phishing", "url")]
    hilang = [c for c in kolom if c not in koreksi.columns]
    if hilang:
        print(f"\n{len(hilang)} fitur tidak ada di koreksi lama "
              f"(ekstraktor berubah sejak itu): {hilang[:5]}")
        print("Koreksi tersebut dilewati supaya kolomnya tetap sejajar.")
        koreksi = koreksi.reindex(columns=dasar.columns)
        koreksi = koreksi.dropna(subset=kolom)
        if len(koreksi) < MINIMAL_KOREKSI:
            print("Setelah disaring, koreksinya tidak cukup lagi.")
            return

    digandakan = pd.concat([koreksi[dasar.columns]] * BOBOT_KOREKSI,
                           ignore_index=True)
    gabungan = pd.concat([dasar, digandakan], ignore_index=True)

    print(f"\nKoreksi digandakan {BOBOT_KOREKSI}x -> {len(digandakan):,} baris")
    print(f"Total data latih  : {len(gabungan):,} baris")

    if not args.latih:
        print("\n(Ini baru pratinjau. Tambahkan --latih untuk benar-benar melatih.)")
        return

    cadangan = DATASET.replace(".csv", "_tanpa_koreksi.csv")
    if not os.path.exists(cadangan):
        dasar.to_csv(cadangan, index=False)
        print(f"\nDataset asli dicadangkan ke: {os.path.basename(cadangan)}")

    gabungan.to_csv(DATASET, index=False)
    print("Dataset diperbarui. Sekarang jalankan:")
    print("    python ml/data/check_leakage.py     (wajib lolos)")
    print("    python ml/models/train_model.py")
    print("    python ml/evaluation/holdout_test.py")
    print("\nBandingkan hasil holdout SEBELUM dan SESUDAH. Kalau angkanya")
    print("turun, kembalikan dataset dari berkas cadangan - koreksinya")
    print("mungkin justru menyesatkan.")


if __name__ == "__main__":
    main()
