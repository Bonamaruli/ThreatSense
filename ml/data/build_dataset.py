"""
build_dataset.py  (versi 2)
===========================
Menyusun dataset latih untuk detektor URL, dengan pencegahan kebocoran
dibangun langsung ke dalam prosesnya.

KENAPA VERSI 1 DIBUANG
----------------------
Versi 1 memakai PhiUSIIL apa adanya: sisi legitimate DAN sisi phishing-nya.
Masalahnya, kedua sisi itu dikumpulkan dengan cara berbeda:

    sisi legitimate -> daftar situs mapan, ditulis sebagai domain polos https
    sisi phishing   -> tangkapan mentah umpan ancaman, lengkap dengan path

Dari 235.795 baris, NOL URL legitimate yang memakai http atau punya path.
Model yang dilatih di situ mencetak 99,55% saat ujian, tapi cuma 69,2% saat
diberi URL sungguhan.

CARA VERSI 2 MENCEGAHNYA
------------------------
1. Sisi legitimate diganti dengan Tranco, dan diambil MENYEBAR dari
   peringkat 1 sampai 1.000.000. Jadi bukan cuma situs terkenal, tapi juga
   domain biasa yang jarang terdengar. Kalau semua contoh "aman" adalah
   situs besar, model cuma belajar mengenali situs besar.

2. Dari PhiUSIIL hanya diambil sisi PHISHING-nya. Sisi legitimate-nya
   dibuang total karena itulah sumber kebocorannya.

3. Fitur dihitung hanya dari nama domain (lihat ml/features/url_features.py),
   jadi perbedaan path dan protokol tidak bisa lagi bocor ke model.

4. Domain phishing yang menumpang hosting bersama (firebaseapp.com,
   weeblysite.com, dan sejenisnya) DIBUANG. Alasannya: domain induknya
   sendiri sah dan ada di Tranco, jadi kalau ikut dipakai, model cuma
   belajar "nama hosting gratis = jahat" - jalan pintas baru. Menangkap
   penyalahgunaan hosting bersama butuh analisis isi halaman, bukan
   analisis nama domain. Batasan ini ditulis terus terang di laporan.

5. Hasilnya WAJIB lolos ml/data/check_leakage.py sebelum dipakai training.

CARA PAKAI
----------
    python ml/data/download_sources.py     (sekali saja)
    python ml/data/build_dataset.py
    python ml/data/check_leakage.py        (wajib lolos)
"""

import os
import sys
import time

import pandas as pd
import tldextract

_current_file = os.path.abspath(__file__)
_project_root = os.path.abspath(os.path.join(_current_file, "..", "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from ml.features.url_features import extract_url_features  # noqa: E402

RAW_DIR = os.path.join(_project_root, "ml", "data", "raw")
OUT_PATH = os.path.join(_project_root, "ml", "data", "processed", "dataset_features.csv")

TRANCO_PATH = os.path.join(RAW_DIR, "tranco_top1m.csv")
PHIUSIIL_PATH = os.path.join(RAW_DIR, "phiusiil_raw.csv")

JUMLAH_PER_KELAS = 20000
RANDOM_SEED = 42

# Domain phishing yang induknya masuk peringkat sekian teratas Tranco
# dianggap "menumpang hosting bersama" dan dibuang (lihat poin 4 di atas).
BATAS_HOSTING_BERSAMA = 200000

_ext = tldextract.TLDExtract(suffix_list_urls=())


def _registrable(host: str) -> str:
    """Ambil domain terdaftarnya saja: 'a.b.contoh.co.id' -> 'contoh.co.id'."""
    e = _ext(host)
    return f"{e.domain}.{e.suffix}" if e.domain and e.suffix else ""


def _bersihkan_host(nilai: str) -> str:
    """Ambil hostname dari URL/domain, buang 'www.' di depan."""
    s = str(nilai).strip().lower()
    s = s.split("//")[-1]          # buang skema
    s = s.split("/")[0]            # buang path
    s = s.split("?")[0].split("#")[0]
    s = s.split(":")[0]            # buang port
    if s.startswith("www."):
        s = s[4:]
    return s


def muat_legitimate() -> pd.DataFrame:
    """
    Ambil domain aman dari Tranco, MENYEBAR di seluruh rentang peringkat.

    Kenapa menyebar dan bukan ambil 20.000 teratas: 20.000 teratas isinya
    situs raksasa dunia yang namanya pendek dan rapi. Model yang dilatih di
    situ akan menganggap semua domain panjang atau tidak terkenal sebagai
    berbahaya - persis kesalahan yang mau kita hindari.
    """
    print("\n[1/3] Memuat domain legitimate dari Tranco...")
    df = pd.read_csv(TRANCO_PATH, header=None, names=["rank", "domain"])
    print(f"  tersedia: {len(df):,} domain (peringkat 1 - {df['rank'].max():,})")

    # Ambil merata: satu domain setiap N peringkat
    langkah = max(1, len(df) // JUMLAH_PER_KELAS)
    contoh = df.iloc[::langkah].head(JUMLAH_PER_KELAS).copy()

    contoh["host"] = contoh["domain"].map(_bersihkan_host).map(_registrable)
    contoh = contoh[contoh["host"].str.len() > 3]
    print(f"  diambil : {len(contoh):,} domain, menyebar tiap {langkah} peringkat")
    print(f"  contoh  : {', '.join(contoh['host'].head(3))} ... "
          f"{', '.join(contoh['host'].tail(2))}")
    return contoh[["host"]].assign(label=0)


def muat_phishing(host_legit: set) -> pd.DataFrame:
    """Ambil hostname phishing dari PhiUSIIL, buang yang menumpang hosting bersama."""
    print("\n[2/3] Memuat domain phishing dari PhiUSIIL...")
    df = pd.read_csv(PHIUSIIL_PATH, usecols=["URL", "label"])

    # Di PhiUSIIL: label 0 = phishing, label 1 = legitimate (terbalik dari intuisi)
    phish = df[df["label"] == 0].copy()
    print(f"  tersedia: {len(phish):,} URL phishing")

    # PENTING: dipotong sampai domain INDUK saja, sama seperti sisi legitimate.
    #
    # Tranco hanya berisi domain induk (contoh.com), sedangkan PhiUSIIL
    # menyimpan hostname lengkap (dev-x.contoh.com). Kalau dibiarkan apa
    # adanya, "punya subdomain" langsung berarti phishing - artefak baru
    # yang sama berbahayanya dengan yang lama. Pemeriksaan kebocoran
    # menangkap ini: subdomain_count == 1 muncul di 8.508 baris dan
    # SEMUANYA phishing, tanpa satu pun pengecualian.
    #
    # Konsekuensinya: penyalahgunaan subdomain tidak bisa dipelajari dari
    # data ini. Itu jujur - lebih baik daripada model yang seolah pintar
    # padahal cuma menghitung titik.
    phish["host"] = phish["URL"].map(_bersihkan_host).map(_registrable)
    phish = phish[phish["host"].str.len() > 3]

    # Buang yang menumpang hosting bersama / gratis
    menumpang = phish["host"].isin(host_legit)
    print(f"  dibuang : {int(menumpang.sum()):,} yang menumpang hosting bersama")
    phish = phish[~menumpang]

    phish = phish.drop_duplicates(subset=["host"])
    print(f"  tersisa : {len(phish):,} domain phishing unik")

    ambil = min(JUMLAH_PER_KELAS, len(phish))
    contoh = phish.sample(ambil, random_state=RANDOM_SEED)
    print(f"  diambil : {len(contoh):,}")
    return contoh[["host"]].assign(label=1)


def ekstrak_fitur(df: pd.DataFrame) -> pd.DataFrame:
    print("\n[3/3] Mengekstrak fitur dari setiap domain...")
    mulai = time.time()

    baris, gagal = [], 0
    for host in df["host"]:
        try:
            baris.append(extract_url_features(host))
        except Exception:
            baris.append(None)
            gagal += 1

    fitur = pd.DataFrame(baris)
    fitur["is_phishing"] = df["label"].values
    fitur["url"] = df["host"].values

    sebelum = len(fitur)
    fitur = fitur.dropna().reset_index(drop=True)
    if sebelum != len(fitur):
        print(f"  dibuang {sebelum - len(fitur):,} baris yang gagal diekstrak")

    print(f"  selesai dalam {time.time()-mulai:.1f} detik ({gagal} gagal)")
    return fitur


def main():
    for p, nama in ((TRANCO_PATH, "Tranco"), (PHIUSIIL_PATH, "PhiUSIIL")):
        if not os.path.exists(p):
            print(f"ERROR: berkas {nama} tidak ada di {p}")
            print("Jalankan dulu: python ml/data/download_sources.py")
            sys.exit(1)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    print("=" * 68)
    print("MEMBANGUN DATASET (versi 2 - level domain)")
    print("=" * 68)

    legit = muat_legitimate()
    host_legit = set(legit["host"].map(_registrable))
    phish = muat_phishing(host_legit)

    gabungan = pd.concat([legit, phish], ignore_index=True)

    # Buang domain yang muncul di dua kelas sekaligus - label bertentangan
    bentrok = gabungan[gabungan.duplicated(subset=["host"], keep=False)]
    if len(bentrok):
        print(f"\n  {len(bentrok):,} domain muncul di dua kelas -> dibuang semua")
        gabungan = gabungan.drop_duplicates(subset=["host"], keep=False)

    gabungan = gabungan.sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)

    fitur = ekstrak_fitur(gabungan)
    fitur.to_csv(OUT_PATH, index=False)

    print("\n" + "=" * 68)
    print(f"Dataset tersimpan: {OUT_PATH}")
    print(f"  {len(fitur):,} baris x {len(fitur.columns) - 2} fitur")
    sebaran = fitur["is_phishing"].value_counts().to_dict()
    print(f"  aman: {sebaran.get(0, 0):,}  |  phishing: {sebaran.get(1, 0):,}")
    print("\nLANGKAH WAJIB BERIKUTNYA:")
    print("    python ml/data/check_leakage.py")
    print("Jangan latih model sebelum pemeriksaan itu lolos.")
    print("=" * 68)


if __name__ == "__main__":
    main()
