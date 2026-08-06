"""
train_deep_model.py
===================
Melatih model pada BUKTI hasil membuka alamat, bukan cuma nama domainnya.

KENAPA MODEL KEDUA, BUKAN MENGGANTI YANG LAMA
---------------------------------------------
Keduanya menjawab pertanyaan berbeda dan dipakai di saat berbeda:

  model nama domain : cepat (0,1 detik), dipakai untuk pemindaian kilat
  model bukti       : lambat (3-8 detik), dipakai saat pengguna minta
                      pemeriksaan mendalam

Model bukti diberi fitur yang benar-benar bisa membedakan hal yang dari
namanya tampak sama:

    toko baru resmi : umur 5 hari, tanpa kolom sandi, isi katalog produk
    phishing baru   : umur 5 hari, ADA kolom sandi, menyebut nama bank

Gabungan seperti itu yang tidak bisa ditulis sebagai aturan sederhana - dan
justru di situlah machine learning benar-benar memberi nilai tambah,
bukan sekadar hiasan.

CARA PAKAI
----------
    python ml/data/build_deep_dataset.py --jumlah 2000
    python ml/data/check_leakage.py --dataset ml/data/processed/deep_features.csv
    python ml/models/train_deep_model.py
"""

import json
import os
import pickle
import sys

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix, f1_score,
    precision_score, recall_score, roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

DATASET = os.path.join(_ROOT, "ml", "data", "processed", "deep_features.csv")
MODELS_DIR = os.path.join(_ROOT, "ml", "models")
MODEL_PATH = os.path.join(MODELS_DIR, "deep_model.pkl")
META_PATH = os.path.join(MODELS_DIR, "deep_model_metadata.json")

SEED = 42


def main():
    if not os.path.exists(DATASET):
        print(f"ERROR: {DATASET} tidak ada.")
        print("Jalankan dulu: python ml/data/build_deep_dataset.py")
        sys.exit(1)

    df = pd.read_csv(DATASET)
    fitur = [c for c in df.columns if c not in ("is_phishing", "url")]
    X, y = df[fitur], df["is_phishing"]

    print("=" * 68)
    print("MELATIH MODEL PADA BUKTI MENDALAM")
    print("=" * 68)
    print(f"Data   : {len(df):,} baris x {len(fitur)} fitur")
    print(f"Sebaran: {int((y==0).sum())} aman / {int((y==1).sum())} berbahaya")

    if len(df) < 100:
        print("\nPERINGATAN: data terlalu sedikit untuk hasil yang bisa dipercaya.")
        print("Kumpulkan lebih banyak dulu dengan --jumlah yang lebih besar.")

    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=5,           # dangkal supaya tidak menghafal data yang sedikit
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        random_state=SEED,
        eval_metric="logloss",
    )

    # ---------- Penilaian yang jujur lewat validasi silang ----------
    #
    # Dengan data seukuran ini, sekali pembagian train/test bisa memberi
    # angka yang beruntung atau sial. Validasi silang menguji setiap baris
    # tepat sekali sebagai data uji, jadi hasilnya jauh lebih bisa dipercaya.
    print("\nMenguji dengan validasi silang 5 lipatan...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    proba_cv = cross_val_predict(model, X, y, cv=cv, method="predict_proba")[:, 1]
    tebak_cv = (proba_cv >= 0.5).astype(int)

    metrik = {
        "accuracy": accuracy_score(y, tebak_cv),
        "precision": precision_score(y, tebak_cv, zero_division=0),
        "recall": recall_score(y, tebak_cv, zero_division=0),
        "f1_score": f1_score(y, tebak_cv, zero_division=0),
        "roc_auc": roc_auc_score(y, proba_cv),
    }
    print("\nHASIL (validasi silang - angka yang bisa dipercaya):")
    for k, v in metrik.items():
        print(f"  {k:10s} {v*100:6.2f}%")

    cm = confusion_matrix(y, tebak_cv)
    print("\n                 Tebak Aman   Tebak Bahaya")
    print(f"  Asli Aman   {cm[0][0]:>10}   {cm[0][1]:>12}")
    print(f"  Asli Bahaya {cm[1][0]:>10}   {cm[1][1]:>12}")
    print(f"\n{classification_report(y, tebak_cv, target_names=['Aman','Bahaya'], zero_division=0)}")

    # ---------- Ketepatan per tingkat keyakinan ----------
    #
    # Angka inilah yang menentukan kapan model boleh didengar. Model yang
    # akurasinya sedang tapi sangat tepat saat yakin tetap berguna - asal
    # tebakan ragu-ragunya diabaikan.
    print("Ketepatan pada berbagai tingkat keyakinan:")
    kalibrasi = {}
    for t in (0.5, 0.7, 0.8, 0.9, 0.95):
        mask = proba_cv >= t
        n = int(mask.sum())
        if n >= 5:
            tepat = float(y[mask].mean())
            kalibrasi[str(t)] = {"jumlah": n, "ketepatan": tepat}
            print(f"  keyakinan >= {t:.2f}  ->  {n:>4} kasus, {tepat*100:5.1f}% tepat")

    # ---------- Latih model final di seluruh data ----------
    model.fit(X, y)

    penting = sorted(zip(fitur, model.feature_importances_),
                     key=lambda t: -t[1])[:15]
    print("\n15 FITUR PALING BERPENGARUH:")
    for n, v in penting:
        asal = "bukti " if n.startswith("d_") else "nama  "
        print(f"  [{asal}] {n:30s} {v:.4f}")

    n_bukti = sum(1 for n, _ in penting if n.startswith("d_"))
    print(f"\n  {n_bukti} dari 15 berasal dari BUKTI hasil membuka alamat.")
    if n_bukti < 5:
        print("  Catatan: sumbangan bukti masih kecil - kemungkinan datanya")
        print("  belum cukup banyak untuk menampakkan polanya.")

    os.makedirs(MODELS_DIR, exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "feature_columns": fitur,
            "metrics_cv": metrik,
            "kalibrasi": kalibrasi,
            "jumlah_data": len(df),
            "fitur_terpenting": [{"nama": n, "bobot": float(v)} for n, v in penting],
            "dilatih_pada": pd.Timestamp.now().isoformat(),
        }, f, indent=2, ensure_ascii=False)

    print(f"\nModel disimpan   : {os.path.relpath(MODEL_PATH, _ROOT)}")
    print(f"Metadata disimpan: {os.path.relpath(META_PATH, _ROOT)}")


if __name__ == "__main__":
    main()
