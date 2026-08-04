"""
download_sources.py
===================
Mengunduh sumber data mentah untuk melatih detektor URL.

KENAPA TIDAK PAKAI PhiUSIIL SAJA
--------------------------------
Dataset PhiUSIIL (yang dipakai versi pertama) ternyata tidak bisa dipakai
apa adanya. Dari 235.795 barisnya:

    - 0 dari 134.850 URL legitimate memakai http  (semuanya https)
    - 0 dari 134.850 URL legitimate punya path    (semuanya domain polos)

Artinya "http" dan "ada path" otomatis berarti phishing. Model yang dilatih
di atasnya mencetak akurasi 99,55%, tapi saat diuji URL sungguhan hanya
69,2% — github.com/torvalds/linux divonis berbahaya 99,97%.

Akar masalahnya: sisi "aman" PhiUSIIL adalah daftar situs mapan pilihan,
sedangkan sisi "phishing" diambil apa adanya dari umpan ancaman. Dua cara
pengambilan yang berbeda meninggalkan jejak, dan jejak itulah yang dipelajari
model.

SUMBER YANG DIPAKAI SEKARANG
----------------------------
1. Tranco     - peringkat 1 juta domain teratas. Kita ambil menyebar dari
                peringkat 1 sampai 1.000.000, jadi bukan cuma situs terkenal
                tapi juga domain biasa yang jarang didengar. Ini penting:
                kalau semua contoh "aman" adalah situs besar, model cuma
                belajar mengenali situs besar.
2. PhiUSIIL   - hanya sisi PHISHING-nya yang dipakai (100.945 URL). Sisi
                legitimate-nya dibuang karena itulah sumber kebocoran.
3. TrustPositif - daftar blokir resmi Komdigi, 9,4 juta domain.

   PENTING - DATANYA DISENSOR DI SUMBERNYA:
   Setiap domain di daftar ini disamarkan mulai karakter KEDUA, contoh
   bentuknya "s****sqq.com" dan "g****rtogel5.com". Sensornya menghapus
   bagian paling khas dari nama domain, sehingga panjang asli, entropi,
   dan strukturnya ikut hilang. Akibatnya daftar ini TIDAK BISA dipakai
   melatih model yang membaca pola huruf.

   Tapi daftar ini tetap berharga untuk MENGUJI cakupan aturan judi:
   kata kunci seperti "togel", "slot", dan "qq" masih terbaca di bagian
   yang tidak disensor. Dari 9,4 juta domain, 1,25 juta (13,3%) memuat
   kata kunci judi. Angka itu dipakai mengukur seberapa banyak domain
   judi yang berhasil ditangkap aturan kita.

   Karena itu deteksi judi di project ini memakai LAPISAN ATURAN yang
   transparan, bukan model hasil latihan. Pilihan ini juga lebih jujur:
   ciri domain judi memang eksplisit ("slot", "gacor", "maxwin"), jadi
   aturan yang bisa dibaca manusia lebih tepat daripada model kotak hitam.

CARA PAKAI
----------
    python ml/data/download_sources.py
"""

import io
import os
import sys
import zipfile

import requests

_current_file = os.path.abspath(__file__)
_project_root = os.path.abspath(os.path.join(_current_file, "..", "..", ".."))
RAW_DIR = os.path.join(_project_root, "ml", "data", "raw")

TRANCO_URL = "https://tranco-list.eu/top-1m.csv.zip"
TRUSTPOSITIF_URL = "https://trustpositif.komdigi.go.id/assets/db/domains"
OPENPHISH_URL = "https://openphish.com/feed.txt"

TIMEOUT = 120


def _simpan(nama: str, teks: str) -> str:
    path = os.path.join(RAW_DIR, nama)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(teks)
    ukuran = os.path.getsize(path) / 1024
    print(f"  tersimpan: {nama}  ({ukuran:,.0f} KB)")
    return path


def unduh_tranco():
    """Top 1 juta domain paling populer. Format CSV: peringkat,domain"""
    print("\n[1/3] Tranco top 1M (domain legitimate)...")
    r = requests.get(TRANCO_URL, timeout=TIMEOUT)
    r.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        nama_dalam = z.namelist()[0]
        isi = z.read(nama_dalam).decode("utf-8", "replace")

    baris = isi.strip().splitlines()
    print(f"  {len(baris):,} domain diterima")
    return _simpan("tranco_top1m.csv", "\n".join(baris) + "\n")


def unduh_trustpositif():
    """Daftar blokir Komdigi. Isinya campuran; penyaringan judi dilakukan nanti."""
    print("\n[2/3] TrustPositif Komdigi (blocklist resmi)...")
    r = requests.get(TRUSTPOSITIF_URL, timeout=TIMEOUT)
    r.raise_for_status()

    baris = [b.strip().lower() for b in r.text.splitlines() if b.strip()]
    print(f"  {len(baris):,} domain diterima")
    return _simpan("trustpositif_domains.txt", "\n".join(baris) + "\n")


def unduh_openphish():
    """Umpan phishing terkini. Kecil, dipakai sebagai penguji tambahan."""
    print("\n[3/3] OpenPhish feed (phishing terkini)...")
    try:
        r = requests.get(OPENPHISH_URL, timeout=TIMEOUT)
        r.raise_for_status()
        baris = [b.strip() for b in r.text.splitlines() if b.strip()]
        print(f"  {len(baris):,} URL diterima")
        return _simpan("openphish_feed.txt", "\n".join(baris) + "\n")
    except Exception as e:
        print(f"  DILEWATI ({type(e).__name__}) - sumber ini opsional")
        return None


def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    print("=" * 66)
    print("UNDUH SUMBER DATA MENTAH")
    print("=" * 66)
    print(f"Folder tujuan: {RAW_DIR}")

    try:
        unduh_tranco()
        unduh_trustpositif()
        unduh_openphish()
    except requests.RequestException as e:
        print(f"\nGAGAL mengunduh: {e}")
        print("Periksa koneksi internet lalu ulangi.")
        sys.exit(1)

    print("\n" + "=" * 66)
    print("SELESAI. Lanjutkan dengan:")
    print("    python ml/data/build_dataset.py")
    print("=" * 66)


if __name__ == "__main__":
    main()
