"""
run.py
======
Titik jalan backend ThreatSense. Bisa dijalankan DARI MANA SAJA.

MASALAH YANG DIPECAHKAN BERKAS INI
----------------------------------
Perintah lama `uvicorn app.main:app` cuma jalan kalau kamu sudah masuk ke
folder backend/ lebih dulu. Kalau dijalankan dari folder root project,
hasilnya selalu:

    ModuleNotFoundError: No module named 'app'

Sebabnya paket `app` berada di dalam backend/, jadi Python tidak melihatnya
saat perintah dijalankan dari root. Ini juga sumber error yang dulu tercatat
di catatan progres ("Could not import module app.main").

Ditambah lagi backend butuh DUA lokasi sekaligus:
    backend/   -> supaya `app.main` ketemu
    root/      -> supaya `ml.scoring.url` ketemu

Berkas ini mendaftarkan keduanya lebih dulu, baru menyalakan server. Jadi
tidak peduli kamu berada di folder mana saat mengetik perintahnya.

CARA PAKAI
----------
    python run.py                 # mode biasa
    python run.py --reload        # server restart otomatis saat kode diubah
    python run.py --port 8080     # ganti port

Pastikan memakai Python dari virtual environment:
    backend\\venv\\Scripts\\python.exe run.py --reload
"""

import argparse
import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.join(_ROOT, "backend")


def _siapkan_path():
    """
    Daftarkan folder yang dibutuhkan ke jalur pencarian modul Python.

    Urutannya penting: backend/ ditaruh paling depan supaya `app` ketemu
    lebih dulu, baru root untuk `ml`.
    """
    for jalur in (_BACKEND, _ROOT):
        if jalur not in sys.path:
            sys.path.insert(0, jalur)

    # Mode --reload menjalankan ulang server di proses ANAK. Proses anak itu
    # tidak mewarisi sys.path yang kita ubah di atas, jadi jalurnya harus
    # dititipkan lewat variabel lingkungan PYTHONPATH. Tanpa baris ini,
    # --reload akan gagal dengan error 'No module named app' padahal mode
    # biasa jalan normal - kesalahan yang sangat membingungkan.
    lama = os.environ.get("PYTHONPATH", "")
    baru = os.pathsep.join([_BACKEND, _ROOT] + ([lama] if lama else []))
    os.environ["PYTHONPATH"] = baru


def main():
    p = argparse.ArgumentParser(description="Menjalankan backend ThreatSense.")
    p.add_argument("--host", default="127.0.0.1",
                   help="Alamat server (bawaan: 127.0.0.1)")
    p.add_argument("--port", type=int, default=8000,
                   help="Nomor port (bawaan: 8000)")
    p.add_argument("--reload", action="store_true",
                   help="Restart otomatis setiap kode diubah (untuk ngoding)")
    args = p.parse_args()

    if not os.path.isdir(_BACKEND):
        print(f"ERROR: folder backend tidak ditemukan di {_BACKEND}")
        print("Pastikan run.py berada di folder root project ThreatSense.")
        sys.exit(1)

    _siapkan_path()

    try:
        import uvicorn
    except ImportError:
        print("ERROR: uvicorn belum terpasang di Python yang kamu pakai.")
        print("\nKemungkinan besar kamu memakai Python sistem, bukan yang di")
        print("virtual environment. Coba jalankan dengan:")
        print("    backend\\venv\\Scripts\\python.exe run.py --reload")
        sys.exit(1)

    print("=" * 60)
    print("ThreatSense Backend")
    print("=" * 60)
    print(f"  Alamat  : http://{args.host}:{args.port}")
    print(f"  Docs    : http://{args.host}:{args.port}/docs")
    print(f"  Reload  : {'menyala' if args.reload else 'mati'}")
    print("  Berhenti: tekan CTRL+C")
    print("=" * 60)

    # Folder yang dipantau saat --reload dibatasi ke kode saja.
    # Kalau dibiarkan memantau seluruh root, dia ikut mengawasi
    # frontend/node_modules (556 MB) dan ml/data/raw (54 MB) - berat, dan
    # server ikut restart tiap kali dataset ditulis ulang.
    dipantau = [
        os.path.join(_BACKEND, "app"),
        os.path.join(_ROOT, "ml", "features"),
        os.path.join(_ROOT, "ml", "scoring"),
    ]

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        reload_dirs=[d for d in dipantau if os.path.exists(d)] if args.reload else None,
    )


if __name__ == "__main__":
    main()
