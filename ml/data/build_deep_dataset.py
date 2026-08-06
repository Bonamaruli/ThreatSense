"""
build_deep_dataset.py
=====================
Mengumpulkan data latih dengan BENAR-BENAR membuka setiap alamat.

BEDANYA DENGAN build_dataset.py
-------------------------------
build_dataset.py hanya membaca nama domain - cepat (6 detik untuk 40.000
baris) tapi dangkal. Berkas ini membuka setiap alamat satu per satu untuk
mengambil bukti: umur domain, negara server, sertifikat, dan isi halaman.

Konsekuensinya lambat, sekitar 3-8 detik per alamat. Karena itu dijalankan
banyak sekaligus (paralel) supaya 1.000 alamat selesai dalam hitungan menit,
bukan jam.

PENJAGAAN TERHADAP KEBOCORAN
----------------------------
Pelajaran mahal dari dataset pertama: kalau sisi "aman" dan sisi "bahaya"
dikumpulkan dengan cara BERBEDA, model akan mempelajari perbedaan cara
pengumpulannya, bukan ciri ancamannya. Dulu hal itu menghasilkan akurasi
99,55% yang ternyata palsu.

Karena itu di sini kedua sisi diperlakukan sama persis:
  - dibuka dengan pengaturan, batas waktu, dan urutan pemeriksaan yang sama
  - dikumpulkan dalam rentang waktu yang sama
  - alamat yang gagal dibuka DIBUANG dari kedua sisi dengan aturan yang sama
  - BENTUK ALAMATNYA setara: kedua sisi sama-sama berupa halaman dalam,
    lengkap dengan path dan kadang subdomain

Poin terakhir itu ditambahkan setelah percobaan pertama gagal. Waktu itu
sisi aman disusun sebagai domain polos ("http://situs.com") sementara sisi
phishing datang dengan hostname lengkap. Pemeriksa kebocoran langsung
menangkapnya:

    subdomain_count == 1  ->  224 baris (31,7% data), SEMUANYA phishing

Nol URL aman punya subdomain, jadi model tinggal menghitung titik untuk
menebak benar. Kesalahan yang sama persis dengan dataset pertama - dan
tidak akan pernah ketahuan dari nilai akurasi, karena akurasinya justru
terlihat bagus.

Hasilnya tetap WAJIB lolos ml/data/check_leakage.py sebelum dipakai.

CARA PAKAI
----------
    python ml/data/build_deep_dataset.py --jumlah 600
    python ml/data/check_leakage.py --dataset ml/data/processed/deep_features.csv
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests

warnings.filterwarnings("ignore")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from ml.features.deep_vector import vektor_dari_bukti          # noqa: E402
from ml.features.live_features import analisis_mendalam        # noqa: E402
from ml.features.url_features import extract_url_features      # noqa: E402

RAW_DIR = os.path.join(_ROOT, "ml", "data", "raw")
OUT = os.path.join(_ROOT, "ml", "data", "processed", "deep_features.csv")

TRANCO = os.path.join(RAW_DIR, "tranco_top1m.csv")
UMPAN_OPENPHISH = "https://openphish.com/feed.txt"
UMPAN_URLHAUS = "https://urlhaus.abuse.ch/downloads/text_recent/"

# Berapa alamat diperiksa bersamaan. Jangan terlalu besar: selain membebani
# jaringan sendiri, mengetuk terlalu banyak server sekaligus itu tidak sopan
# dan bisa membuat alamat kita diblokir.
PEKERJA = 20


def _unduh_umpan(url: str, batas: int) -> list[str]:
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        baris = [
            l.strip() for l in r.text.splitlines()
            if l.strip() and not l.startswith("#") and l.startswith("http")
        ]
        return baris[:batas]
    except Exception as e:
        print(f"  umpan gagal diunduh ({type(e).__name__}): {url}")
        return []


def _tautan_dari_satu(domain: str, maks: int = 3) -> list[str]:
    """Buka beranda sebuah situs, ambil beberapa tautan ke halaman dalamnya."""
    import httpx
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin, urlparse

    try:
        with httpx.Client(timeout=8, follow_redirects=True, verify=False,
                          headers={"User-Agent": "ThreatSense-Scanner/1.0"}) as c:
            r = c.get("http://" + domain)
        if r.status_code != 200 or "html" not in r.headers.get("content-type", ""):
            return []

        sup = BeautifulSoup(r.content[:1_000_000], "html.parser")
        induk = urlparse(str(r.url)).hostname or ""
        ketemu, terlihat = [], set()

        for a in sup.find_all("a", href=True):
            penuh = urljoin(str(r.url), a["href"])
            p = urlparse(penuh)
            if p.scheme not in ("http", "https") or not p.hostname:
                continue
            # Hanya tautan ke situs itu sendiri
            if induk not in p.hostname and p.hostname not in induk:
                continue
            # Wajib punya path atau subdomain - inilah yang membuat sisi aman
            # setara secara struktur dengan alamat phishing
            if not (len(p.path.strip("/")) > 0 or p.hostname.count(".") > 1):
                continue
            if penuh in terlihat:
                continue
            terlihat.add(penuh)
            ketemu.append(penuh)
            if len(ketemu) >= maks:
                break

        return ketemu
    except Exception:
        return []


def panen_tautan_dalam(benih: list[str], target: int) -> list[str]:
    """
    Kumpulkan alamat halaman DALAM dari situs-situs sah.

    KENAPA TIDAK CUKUP MEMAKAI "http://domain.com" SAJA
    Percobaan pertama memakai domain polos untuk sisi aman, sementara sisi
    phishing datang dengan hostname lengkap berisi subdomain dan path.
    Hasilnya artefak telak - pemeriksa kebocoran menangkapnya:

        subdomain_count == 1  ->  224 baris, SEMUANYA phishing

    Nol URL aman punya subdomain, jadi model tinggal menghitung titik untuk
    menebak dengan benar. Itu bukan belajar mengenali ancaman, melainkan
    belajar cara saya menyusun daftar.

    Dengan memanen tautan dalam, alamat sah jadi berbentuk sama seperti
    alamat yang benar-benar diklik orang - lengkap dengan path dan kadang
    subdomain.
    """
    print(f"  Memanen tautan dalam dari {len(benih)} situs sah...")
    hasil: list[str] = []

    with ThreadPoolExecutor(max_workers=PEKERJA) as ex:
        tugas = {ex.submit(_tautan_dari_satu, d): d for d in benih}
        for t in as_completed(tugas):
            hasil.extend(t.result())
            if len(hasil) >= target:
                break

    return hasil[:target]


def kumpulkan_target(jumlah: int) -> list[tuple[str, int]]:
    """Susun daftar alamat yang akan diperiksa: separuh sah, separuh jahat."""
    per_sisi = jumlah // 2

    print("\n[1/3] Menyiapkan daftar alamat...")

    # --- Sisi JAHAT ---
    jahat: list[str] = []
    jahat += _unduh_umpan(UMPAN_OPENPHISH, per_sisi)
    print(f"  OpenPhish : {len(jahat)} alamat")

    if len(jahat) < per_sisi:
        # URLhaus dipakai sebagai pelengkap, TAPI yang berupa alamat IP mentah
        # dibuang. Kalau ikut dipakai, model gampang belajar jalan pintas
        # "ada angka IP berarti jahat" - dan itu jenis kebocoran yang sama
        # dengan kesalahan dataset pertama.
        import re
        pola_ip = re.compile(r"^https?://\d{1,3}(\.\d{1,3}){3}")
        tambahan = [
            u for u in _unduh_umpan(UMPAN_URLHAUS, per_sisi * 4)
            if not pola_ip.match(u)
        ]
        perlu = per_sisi - len(jahat)
        jahat += tambahan[:perlu]
        print(f"  URLhaus   : +{min(perlu, len(tambahan))} alamat (IP mentah dibuang)")

    # --- Sisi SAH ---
    df = pd.read_csv(TRANCO, header=None, names=["rank", "domain"])
    langkah = max(1, len(df) // (per_sisi * 2))
    benih = list(df.iloc[::langkah].head(per_sisi * 2)["domain"])

    sah = panen_tautan_dalam(benih, per_sisi)
    print(f"  Tranco    : {len(sah)} alamat (hasil panen tautan dalam)")

    target = [(u, 1) for u in jahat] + [(u, 0) for u in sah]
    print(f"  Total     : {len(target)} alamat akan diperiksa")
    return target


def _periksa_satu(url: str, label: int) -> dict | None:
    """Periksa satu alamat. Mengembalikan None kalau tidak layak dipakai."""
    try:
        bukti = analisis_mendalam(url)
    except Exception:
        return None

    # Alamat yang sama sekali tidak bisa dibuka DIBUANG dari kedua sisi.
    #
    # Alasannya penting: alamat phishing cepat ditutup, jadi banyak yang
    # sudah mati saat diperiksa. Kalau yang mati tetap dipakai, model akan
    # belajar "tidak bisa dibuka = phishing" - padahal itu cuma menandakan
    # kita datang terlambat, bukan ciri ancaman.
    if not bukti.get("halaman_terbaca"):
        return None

    baris = extract_url_features(url)          # 31 fitur nama domain
    baris.update(vektor_dari_bukti(bukti))     # + fitur bukti mendalam
    baris["is_phishing"] = label
    baris["url"] = url
    return baris


def kumpulkan(target: list[tuple[str, int]]) -> pd.DataFrame:
    print(f"\n[2/3] Memeriksa {len(target)} alamat ({PEKERJA} sekaligus)...")
    print("      Ini bagian yang lama - tiap alamat benar-benar dibuka.\n")

    hasil: list[dict] = []
    gagal = 0
    mulai = time.time()

    with ThreadPoolExecutor(max_workers=PEKERJA) as ex:
        tugas = {ex.submit(_periksa_satu, u, l): u for u, l in target}
        selesai = 0
        for t in as_completed(tugas):
            selesai += 1
            r = t.result()
            if r:
                hasil.append(r)
            else:
                gagal += 1

            if selesai % 50 == 0 or selesai == len(target):
                lewat = time.time() - mulai
                sisa = (lewat / selesai) * (len(target) - selesai)
                print(f"      {selesai}/{len(target)}  berhasil={len(hasil)} "
                      f"gagal={gagal}  (~{sisa/60:.1f} menit lagi)")

    print(f"\n      Selesai dalam {(time.time()-mulai)/60:.1f} menit")
    print(f"      Berhasil dibuka : {len(hasil)}")
    print(f"      Tidak terjangkau: {gagal} (dibuang dari kedua sisi)")
    return pd.DataFrame(hasil)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--jumlah", type=int, default=600,
                   help="Perkiraan total alamat yang diperiksa")
    args = p.parse_args()

    if not os.path.exists(TRANCO):
        print(f"ERROR: {TRANCO} tidak ada.")
        print("Jalankan dulu: python ml/data/download_sources.py")
        sys.exit(1)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)

    print("=" * 70)
    print("MEMBANGUN DATASET DARI BUKTI NYATA")
    print("=" * 70)

    target = kumpulkan_target(args.jumlah)
    df = kumpulkan(target)

    if df.empty:
        print("\nTidak ada data yang berhasil dikumpulkan.")
        sys.exit(1)

    print("\n[3/3] Menyimpan...")
    sebaran = df["is_phishing"].value_counts().to_dict()
    n_aman, n_jahat = sebaran.get(0, 0), sebaran.get(1, 0)

    # Diseimbangkan supaya model tidak bisa curang dengan selalu menebak
    # kelas yang lebih banyak.
    if n_aman and n_jahat:
        n = min(n_aman, n_jahat)
        df = pd.concat([
            df[df.is_phishing == 0].sample(n, random_state=42),
            df[df.is_phishing == 1].sample(n, random_state=42),
        ]).sample(frac=1, random_state=42).reset_index(drop=True)

    df.to_csv(OUT, index=False)
    print(f"  Tersimpan: {OUT}")
    print(f"  {len(df)} baris x {len(df.columns)-2} fitur")
    print(f"  aman: {int((df.is_phishing==0).sum())} | "
          f"berbahaya: {int((df.is_phishing==1).sum())}")

    print("\nLANGKAH WAJIB BERIKUTNYA:")
    print(f"  python ml/data/check_leakage.py --dataset {os.path.relpath(OUT, _ROOT)}")
    print("Jangan latih model sebelum pemeriksaan itu lolos.")


if __name__ == "__main__":
    main()
