"""
check_leakage.py
================
Pemeriksa KEBOCORAN DATASET (data leakage) untuk dataset deteksi URL.

APA ITU KEBOCORAN DATASET
-------------------------
Kebocoran terjadi saat dataset punya "jalan pintas" yang membuat model
tampak pintar padahal tidak. Contoh nyata yang ditemukan di project ini:

    Di dataset PhiUSIIL, 10.000 dari 10.000 URL legitimate memakai https,
    dan 10.000 dari 10.000 URL legitimate tidak punya path sama sekali.

Akibatnya model tidak belajar "seperti apa ciri phishing". Model cuma
belajar "http berarti phishing" dan "ada garis miring berarti phishing".
Nilai akurasinya 99,55% — tapi saat diuji dengan URL sungguhan, situs
github.com/torvalds/linux dan bps.go.id ikut divonis berbahaya 99,9%.

Ini bukan kesalahan pemrograman. Ini kesalahan pengumpulan data, dan
tidak akan pernah ketahuan dari nilai akurasi. Justru sebaliknya:
makin parah kebocorannya, makin tinggi akurasinya, makin meyakinkan
kelihatannya. Itulah yang membuatnya berbahaya.

CARA PAKAI
----------
    python ml/data/check_leakage.py
    python ml/data/check_leakage.py --dataset path/ke/dataset_lain.csv

JALANKAN INI SEBELUM SETIAP TRAINING. Kalau hasilnya BOCOR, perbaiki
dulu datasetnya — melatih model di atas dataset bocor cuma membuang waktu.
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import cross_val_score

_current_file = os.path.abspath(__file__)
_project_root = os.path.abspath(os.path.join(_current_file, "..", "..", ".."))

DEFAULT_DATASET = os.path.join(
    _project_root, "ml", "data", "processed", "dataset_features.csv"
)

LABEL_COL = "is_phishing"
NON_FEATURE_COLS = (LABEL_COL, "url")

# Ambang batas penilaian.
# Kalau SATU fitur saja sudah bisa menebak sebaik ini, hampir pasti
# fitur itu bukan sinyal asli melainkan jejak cara data dikumpulkan.
AMBANG_FITUR_TUNGGAL = 0.85
AMBANG_ATURAN_SEDERHANA = 0.90

# Seberapa luas sebuah "pemisah sempurna" harus mencakup data sebelum
# dianggap kebocoran sungguhan.
#
# Kenapa perlu ambang ini: tidak semua pemisah sempurna itu artefak. Contoh
# nyata dari dataset ini - domain yang memuat DUA kata kunci phishing
# sekaligus ("secure-login-verify") memang semuanya phishing, tapi cuma ada
# 59 baris (0,15%). Itu bukan cacat pengumpulan data, melainkan pola langka
# yang kebetulan sangat menentukan.
#
# Bandingkan dengan artefak sungguhan yang sempat ditemukan: subdomain_count
# == 1 mencakup 8.508 baris (21%) dan semuanya phishing - itu jelas jejak
# cara pengumpulan data, bukan ciri phishing.
#
# Jadi: cakupan luas = artefak, cakupan sempit = pola langka yang wajar.
AMBANG_CAKUPAN_PEMISAH = 0.01  # 1% dari total baris


def _garis(judul=""):
    print("\n" + "=" * 72)
    if judul:
        print(judul)
        print("=" * 72)


def cek_fitur_tunggal(X: pd.DataFrame, y: pd.Series) -> list[tuple[str, float]]:
    """
    Uji tiap fitur SENDIRIAN memakai pohon keputusan sedalam 1 tingkat.

    Pohon sedalam 1 hanya bisa bertanya satu kali, misalnya "apakah
    url_length > 40?". Kalau pertanyaan setipis itu saja sudah bisa
    memisahkan phishing dari aman dengan akurasi tinggi, berarti ada
    jalan pintas di datasetmu.
    """
    hasil = []
    for kolom in X.columns:
        stump = DecisionTreeClassifier(max_depth=1, random_state=42)
        skor = cross_val_score(
            stump, X[[kolom]], y, cv=5, scoring="accuracy", n_jobs=-1
        ).mean()
        hasil.append((kolom, skor))

    return sorted(hasil, key=lambda t: t[1], reverse=True)


def cek_pemisah_sempurna(X: pd.DataFrame, y: pd.Series) -> tuple[list[str], list[str]]:
    """
    Cari fitur biner yang salah satu nilainya HANYA muncul di satu kelas.

    Inilah bentuk kebocoran paling parah. Contoh dari PhiUSIIL:
    tidak ada satu pun URL legitimate yang memakai http, sehingga
    "http" otomatis berarti phishing dengan kepastian 100%.
    """
    parah, ringan = [], []
    batas_baris = max(50, int(len(X) * AMBANG_CAKUPAN_PEMISAH))

    for kolom in X.columns:
        nilai_unik = X[kolom].dropna().unique()
        if len(nilai_unik) > 10:  # lewati fitur kontinu
            continue

        for nilai in nilai_unik:
            mask = X[kolom] == nilai
            jumlah = int(mask.sum())
            if jumlah < 50:  # terlalu sedikit, bukan pola bermakna
                continue

            rasio = y[mask].mean()  # 1.0 = semua phishing, 0.0 = semua aman
            if rasio in (0.0, 1.0):
                kelas = "SEMUA phishing" if rasio == 1.0 else "SEMUA aman"
                cakupan = jumlah / len(X) * 100
                pesan = (
                    f"{kolom} == {nilai}  ->  {kelas} "
                    f"({jumlah:,} baris = {cakupan:.1f}% data)"
                )
                (parah if jumlah >= batas_baris else ringan).append(pesan)

    return parah, ringan


def cek_aturan_sederhana(X: pd.DataFrame, y: pd.Series) -> float:
    """
    Seberapa jauh pohon keputusan yang SANGAT dangkal (2 tingkat) bisa
    melangkah? Pohon ini setara dengan tulisan tangan beberapa baris if.

    Kalau hasilnya sudah mendekati akurasi model XGBoost-mu, artinya
    seluruh kerumitan model itu tidak menambah apa pun — datasetnya
    memang terlalu mudah ditebak.
    """
    pohon = DecisionTreeClassifier(max_depth=2, random_state=42)
    return cross_val_score(pohon, X, y, cv=5, scoring="accuracy", n_jobs=-1).mean()


def cek_duplikat(df: pd.DataFrame) -> tuple[int, int]:
    """URL kembar, dan yang lebih buruk: URL sama dengan label berbeda."""
    if "url" not in df.columns:
        return 0, 0

    duplikat = int(df.duplicated(subset=["url"]).sum())
    bentrok = 0
    if duplikat:
        per_url = df.groupby("url")[LABEL_COL].nunique()
        bentrok = int((per_url > 1).sum())

    return duplikat, bentrok


def main():
    parser = argparse.ArgumentParser(
        description="Deteksi kebocoran pada dataset deteksi URL."
    )
    parser.add_argument("--dataset", default=DEFAULT_DATASET,
                        help="Path ke file CSV dataset berfitur.")
    args = parser.parse_args()

    if not os.path.exists(args.dataset):
        print(f"ERROR: dataset tidak ditemukan di {args.dataset}")
        print("Jalankan dulu: python ml/data/build_dataset.py")
        sys.exit(1)

    df = pd.read_csv(args.dataset)
    fitur = [c for c in df.columns if c not in NON_FEATURE_COLS]
    X, y = df[fitur], df[LABEL_COL]

    _garis("PEMERIKSAAN KEBOCORAN DATASET")
    print(f"Berkas   : {args.dataset}")
    print(f"Ukuran   : {len(df):,} baris x {len(fitur)} fitur")
    sebaran = y.value_counts().to_dict()
    print(f"Sebaran  : {sebaran.get(0, 0):,} aman / {sebaran.get(1, 0):,} phishing")

    masalah = []

    # ---------- 1. Pemisah sempurna ----------
    _garis("1. FITUR YANG MEMISAHKAN SECARA SEMPURNA")
    print("Mencari nilai fitur yang HANYA pernah muncul di satu kelas saja.\n")
    parah, ringan = cek_pemisah_sempurna(X, y)
    if parah:
        for p in parah:
            print(f"  [BOCOR] {p}")
        masalah.append(f"{len(parah)} pemisah sempurna berdampak luas")
    else:
        print("  Aman: tidak ada pemisah sempurna yang mencakup banyak data.")

    if ringan:
        print(f"\n  Catatan - {len(ringan)} pemisah sempurna bercakupan sempit "
              f"(di bawah {AMBANG_CAKUPAN_PEMISAH*100:.0f}% data):")
        for p in ringan:
            print(f"    - {p}")
        print("  Ini WAJAR: pola langka yang kebetulan sangat menentukan,")
        print("  bukan jejak cara pengumpulan data. Tidak dihitung kebocoran.")

    # ---------- 2. Fitur tunggal ----------
    _garis("2. KEKUATAN TIAP FITUR SENDIRIAN")
    print("Akurasi bila model HANYA boleh melihat satu fitur ini saja.\n")
    peringkat = cek_fitur_tunggal(X, y)
    for nama, skor in peringkat[:8]:
        tanda = "  <-- MENCURIGAKAN" if skor >= AMBANG_FITUR_TUNGGAL else ""
        print(f"  {nama:28s} {skor*100:6.2f}%{tanda}")

    tersangka = [n for n, s in peringkat if s >= AMBANG_FITUR_TUNGGAL]
    if tersangka:
        masalah.append(f"{len(tersangka)} fitur terlalu kuat sendirian")

    # ---------- 3. Aturan dangkal ----------
    _garis("3. SEBERAPA MUDAH DATASET INI DITEBAK")
    dangkal = cek_aturan_sederhana(X, y)
    print(f"  Akurasi pohon keputusan 2 tingkat : {dangkal*100:.2f}%")
    print("  (pohon sedangkal ini setara beberapa baris if biasa)")
    if dangkal >= AMBANG_ATURAN_SEDERHANA:
        print("\n  [BOCOR] Aturan sesederhana ini seharusnya TIDAK sekuat itu.")
        print("          Kalau XGBoost-mu hanya unggul tipis dari angka di atas,")
        print("          berarti model rumitmu tidak menambah nilai apa pun.")
        masalah.append("dataset tertebak oleh aturan dangkal")
    else:
        print("  Wajar: dataset tidak bisa ditebak hanya dengan aturan dangkal.")

    # ---------- 4. Duplikat ----------
    _garis("4. DUPLIKAT")
    duplikat, bentrok = cek_duplikat(df)
    print(f"  URL kembar                : {duplikat:,}")
    print(f"  URL kembar berlabel beda  : {bentrok:,}")
    if duplikat:
        masalah.append(f"{duplikat} URL kembar")
    if bentrok:
        masalah.append(f"{bentrok} URL berlabel bertentangan")

    # ---------- KESIMPULAN ----------
    _garis("KESIMPULAN")
    if masalah:
        print("  STATUS: DATASET BOCOR\n")
        for m in masalah:
            print(f"    - {m}")
        print("\n  JANGAN latih model di atas dataset ini dulu. Nilai akurasi")
        print("  yang keluar nanti akan tinggi tapi menyesatkan, dan modelnya")
        print("  akan gagal begitu diuji dengan URL sungguhan.")
        print("\n  Langkah perbaikan: pastikan cara pengumpulan URL aman dan URL")
        print("  phishing SAMA. Kalau URL amanmu diambil sebagai domain polos")
        print("  (https://situs.com) sementara URL phishing diambil lengkap")
        print("  dengan path (http://situs.com/login/verify), maka yang dipelajari")
        print("  model adalah cara kamu mengumpulkan data, BUKAN ciri phishing.")
        sys.exit(1)
    else:
        print("  STATUS: TIDAK DITEMUKAN KEBOCORAN YANG JELAS\n")
        print("  Dataset ini layak dipakai training. Tetap uji model akhirnya")
        print("  dengan ml/evaluation/holdout_test.py memakai URL sungguhan.")
        sys.exit(0)


if __name__ == "__main__":
    main()
