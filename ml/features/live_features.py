"""
live_features.py
================
Analisis MENDALAM sebuah alamat: benar-benar masuk ke dalamnya, bukan
sekadar membaca namanya.

KENAPA MODUL INI ADA
--------------------
Analisis nama domain saja punya batas keras yang sudah terbukti dengan
angka. Saat 500 domain sah tidak terkenal diperiksa, yang benar-benar
memutuskan ternyata:

    tidak ada sinyal apa pun -> dianggap aman   471 (94,2%)
    aturan kata kunci                             28 (5,6%)
    model machine learning                         1 (0,2%)

Artinya sistem lama hampir selalu menjawab "aman" hanya karena tidak
menemukan kata mencurigakan di nama domainnya. Sebuah halaman login BRI
palsu di "tokobungamelati.com" akan lolos begitu saja - namanya polos.

Modul ini mengumpulkan BUKTI, bukan tebakan dari nama:

    Dari pendaftaran : umur domain, negara, registrar
    Dari jaringan    : alamat IP, negara hosting, penyedia layanan
    Dari keamanan    : sertifikat SSL, umur dan penerbitnya
    Dari perilaku    : apa yang terjadi kalau diklik (rantai pengalihan)
    Dari isi halaman : kolom sandi, form yang mengirim ke domain lain,
                       kata judi di teks, peniruan merek, iframe tersembunyi

Kombinasi inilah yang menjawab pertanyaan "bagaimana kalau domain resmi
yang baru?". Umur 3 hari saja tidak berarti apa-apa. Umur 3 hari DITAMBAH
kolom sandi DITAMBAH menyebut nama bank tapi bukan domain bank itu -
barulah kesimpulannya kuat.

BATAS KEAMANAN YANG DIPASANG
----------------------------
Membuka halaman yang mungkin berbahaya harus dilakukan dengan hati-hati:

  - JavaScript TIDAK dijalankan. Halaman hanya diunduh dan dibaca sebagai
    teks. Ini yang membuatnya aman - kode di halaman tidak pernah hidup.
  - Batas waktu ketat, supaya tidak menggantung selamanya
  - Batas ukuran unduhan, supaya berkas raksasa tidak menghabiskan memori
  - Hanya http dan https yang diikuti
  - Setiap tahap gagal sendiri-sendiri: WHOIS mati tidak membatalkan
    pembacaan halaman
"""

from __future__ import annotations

import re
import socket
import ssl
from datetime import datetime, timezone
from typing import Any

import httpx
from bs4 import BeautifulSoup

from ml.features.jaringan_aman import aman_dibuka
from ml.features.url_features import (
    BRANDS,
    JUDOL_KEYWORDS,
    JUDOL_KEYWORDS_KUAT,
    normalisasi_url,
)

# ============================================================
# BATAS KEAMANAN
# ============================================================

BATAS_WAKTU_DETIK = 10
BATAS_UNDUH_BYTE = 2 * 1024 * 1024      # 2 MB sudah lebih dari cukup
BATAS_PENGALIHAN = 10

# Diperkenalkan apa adanya sebagai pemindai, bukan menyamar jadi peramban.
# Menyamar akan membuat hasilnya tidak jujur dan berpotensi melanggar
# ketentuan situs yang diperiksa.
USER_AGENT = "ThreatSense-Scanner/1.0 (+pemindai keamanan; tidak menjalankan skrip)"

# Kata yang menandakan halaman meminta kredensial
KATA_KREDENSIAL = [
    "password", "kata sandi", "katasandi", "sandi", "pin", "otp",
    "verifikasi", "verification", "login", "masuk", "sign in",
    "username", "nama pengguna", "no rekening", "nomor rekening",
    "cvv", "atm", "mpin", "token",
]

# Pola JavaScript yang sengaja diacak agar isinya sulit dibaca.
# Bukan bukti kejahatan (banyak situs memampatkan kodenya), tapi jadi
# petunjuk tambahan bila muncul bersama tanda lain.
POLA_JS_TERACAK = [
    re.compile(r"eval\s*\(\s*(?:atob|unescape|decodeURIComponent)", re.I),
    re.compile(r"document\.write\s*\(\s*unescape", re.I),
    re.compile(r"fromCharCode\s*\((?:\s*\d+\s*,){12,}", re.I),
    re.compile(r"\\x[0-9a-f]{2}(?:\\x[0-9a-f]{2}){25,}", re.I),
]

_ENDPOINT_GEO = "http://ip-api.com/json/{ip}?fields=status,country,countryCode,isp,org"


# ============================================================
# HELPER
# ============================================================

def _hasil_kosong() -> dict[str, Any]:
    """
    Bentuk hasil bawaan.

    Semua kunci SELALU ada walau pemeriksaannya gagal, supaya pemakainya
    tidak perlu menulis pengecekan "ada tidaknya kunci" di mana-mana.
    Nilai None berarti "tidak berhasil diperiksa", berbeda dari 0 atau
    False yang berarti "diperiksa, hasilnya memang nol".
    """
    return {
        # Pendaftaran domain
        "umur_domain_hari": None,
        "negara_pendaftar": None,
        "registrar": None,
        "tanggal_dibuat": None,
        # Jaringan
        "ip": None,
        "negara_hosting": None,
        "kode_negara_hosting": None,
        "isp": None,
        # Keamanan
        "ssl_ada": None,
        "ssl_penerbit": None,
        "ssl_umur_hari": None,
        "ssl_cocok_domain": None,
        # Perilaku saat diklik
        "status_http": None,
        "jumlah_pengalihan": 0,
        "url_akhir": None,
        "pindah_domain": False,
        "rantai_pengalihan": [],
        # Isi halaman
        "halaman_terbaca": False,
        "judul_halaman": None,
        "ada_kolom_sandi": False,
        "jumlah_kolom_sandi": 0,
        "jumlah_form": 0,
        "form_kirim_ke_domain_lain": False,
        "tujuan_form_asing": None,
        "kata_kredensial_di_halaman": 0,
        "kata_judi_di_halaman": 0,
        "kata_judi_kuat_di_halaman": 0,
        "merek_disebut_di_halaman": None,
        "iframe_tersembunyi": 0,
        "js_teracak": False,
        "ukuran_halaman": 0,
        # Penanda apakah bagian domain diambil dari simpanan, bukan diperiksa
        # ulang. Ditampilkan apa adanya supaya pengguna tahu umur domain yang
        # dilihatnya bisa terlambat beberapa hari.
        "dari_cache": False,
        # Catatan kegagalan, supaya bisa dijelaskan ke pengguna
        "kegagalan": [],
    }


def _domain_dari(url: str) -> str:
    import tldextract
    e = tldextract.TLDExtract(suffix_list_urls=())(url)
    return f"{e.domain}.{e.suffix}".lower() if e.domain and e.suffix else ""


def _ke_datetime(nilai) -> datetime | None:
    """
    Ubah nilai tanggal dari WHOIS jadi datetime.

    Pustaka whois kadang mengembalikan satu tanggal, kadang DAFTAR tanggal
    (karena beberapa server WHOIS menjawab berbeda-beda). Kalau daftarnya
    tidak ditangani, perbandingan tanggal langsung gagal.
    """
    if nilai is None:
        return None
    if isinstance(nilai, list):
        nilai = next((v for v in nilai if v), None)
        if nilai is None:
            return None
    if isinstance(nilai, datetime):
        return nilai.replace(tzinfo=None) if nilai.tzinfo else nilai
    return None


# ============================================================
# TAHAP PEMERIKSAAN
# ============================================================

def _periksa_whois(domain: str, h: dict) -> None:
    """Umur domain, negara pendaftaran, dan registrar."""
    try:
        import whois
        w = whois.whois(domain)

        dibuat = _ke_datetime(getattr(w, "creation_date", None))
        if dibuat:
            h["tanggal_dibuat"] = dibuat.strftime("%Y-%m-%d")
            h["umur_domain_hari"] = (datetime.utcnow() - dibuat).days

        negara = getattr(w, "country", None)
        if isinstance(negara, list):
            negara = negara[0] if negara else None
        h["negara_pendaftar"] = str(negara) if negara else None

        reg = getattr(w, "registrar", None)
        if isinstance(reg, list):
            reg = reg[0] if reg else None
        h["registrar"] = str(reg)[:80] if reg else None

    except Exception as e:
        h["kegagalan"].append(f"WHOIS tidak terbaca ({type(e).__name__})")


def _periksa_jaringan(hostname: str, h: dict) -> None:
    """Alamat IP, negara tempat server berada, dan penyedia layanannya."""
    try:
        h["ip"] = socket.gethostbyname(hostname)
    except Exception as e:
        h["kegagalan"].append(f"Alamat IP tidak ditemukan ({type(e).__name__})")
        return

    try:
        with httpx.Client(timeout=8) as c:
            d = c.get(_ENDPOINT_GEO.format(ip=h["ip"])).json()
        if d.get("status") == "success":
            h["negara_hosting"] = d.get("country")
            h["kode_negara_hosting"] = d.get("countryCode")
            h["isp"] = (d.get("isp") or d.get("org") or None)
    except Exception:
        # Lokasi server hanya pelengkap; kegagalannya tidak perlu dilaporkan
        pass


def _periksa_ssl(hostname: str, h: dict) -> None:
    """Sertifikat SSL: ada tidaknya, penerbit, umur, dan kecocokan nama."""
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=8) as s:
            with ctx.wrap_socket(s, server_hostname=hostname) as ss:
                sert = ss.getpeercert()

        h["ssl_ada"] = True
        h["ssl_cocok_domain"] = True  # wrap_socket gagal kalau tidak cocok

        penerbit = dict(x[0] for x in sert.get("issuer", ()))
        h["ssl_penerbit"] = penerbit.get("organizationName") or penerbit.get("commonName")

        mulai = sert.get("notBefore")
        if mulai:
            t = datetime.strptime(mulai, "%b %d %H:%M:%S %Y %Z")
            h["ssl_umur_hari"] = (datetime.utcnow() - t).days

    except ssl.SSLCertVerificationError:
        # Sertifikat ADA tapi tidak sah - ini justru temuan penting
        h["ssl_ada"] = True
        h["ssl_cocok_domain"] = False
    except Exception:
        h["ssl_ada"] = False


def _ambil_halaman(url: str, h: dict) -> str | None:
    """
    Buka halamannya dan catat apa yang terjadi - inilah "kalau diklik".

    JavaScript tidak dijalankan sama sekali; halaman hanya diunduh sebagai
    teks lalu dibaca. Itulah yang membuat langkah ini aman dilakukan
    terhadap alamat yang belum diketahui aman.
    """
    try:
        # Pengalihan TIDAK diikuti otomatis, melainkan ditelusuri satu per
        # satu. Alasannya keamanan: alamat luar yang tampak wajar bisa
        # mengalihkan ke alamat internal di langkah berikutnya. Kalau
        # pengalihan diserahkan ke pustaka, langkah-langkah itu tidak pernah
        # sempat diperiksa.
        riwayat: list[str] = []
        sekarang = url

        with httpx.Client(
            timeout=BATAS_WAKTU_DETIK,
            follow_redirects=False,
            headers={"User-Agent": USER_AGENT},
            verify=False,   # sertifikat rusak diperiksa terpisah di _periksa_ssl
        ) as c:
            for _ in range(BATAS_PENGALIHAN + 1):
                aman, alasan = aman_dibuka(sekarang)
                if not aman:
                    h["kegagalan"].append(f"Dihentikan demi keamanan: {alasan}")
                    return None

                r = c.get(sekarang)

                if r.status_code in (301, 302, 303, 307, 308):
                    tujuan = r.headers.get("location")
                    if not tujuan:
                        break
                    riwayat.append(sekarang)
                    sekarang = str(httpx.URL(sekarang).join(tujuan))
                    continue
                break
            else:
                h["kegagalan"].append("Pengalihan berputar tanpa henti")
                return None

        h["status_http"] = r.status_code
        h["jumlah_pengalihan"] = len(riwayat)
        h["url_akhir"] = sekarang
        h["rantai_pengalihan"] = riwayat[:BATAS_PENGALIHAN]

        awal, akhir = _domain_dari(url), _domain_dari(sekarang)
        h["pindah_domain"] = bool(awal and akhir and awal != akhir)

        isi = r.content[:BATAS_UNDUH_BYTE]
        h["ukuran_halaman"] = len(isi)

        jenis = r.headers.get("content-type", "")
        if "html" not in jenis.lower() and "text" not in jenis.lower():
            h["kegagalan"].append(f"Bukan halaman web (tipe: {jenis[:40]})")
            return None

        return isi.decode(r.encoding or "utf-8", errors="replace")

    except httpx.TooManyRedirects:
        h["kegagalan"].append("Pengalihan berputar tanpa henti")
    except httpx.TimeoutException:
        h["kegagalan"].append("Halaman tidak menjawab dalam batas waktu")
    except Exception as e:
        h["kegagalan"].append(f"Halaman tidak bisa dibuka ({type(e).__name__})")
    return None


def _baca_isi_halaman(html: str, url_akhir: str, h: dict) -> None:
    """Cari bukti di dalam halaman: form, kolom sandi, kata kunci, merek."""
    try:
        sup = BeautifulSoup(html, "html.parser")
    except Exception as e:
        h["kegagalan"].append(f"Isi halaman tidak terbaca ({type(e).__name__})")
        return

    h["halaman_terbaca"] = True

    if sup.title and sup.title.string:
        h["judul_halaman"] = sup.title.string.strip()[:200]

    # --- Kolom sandi: tanda paling langsung bahwa halaman meminta kredensial
    sandi = sup.find_all("input", attrs={"type": re.compile("^password$", re.I)})
    h["jumlah_kolom_sandi"] = len(sandi)
    h["ada_kolom_sandi"] = len(sandi) > 0

    # --- Form yang mengirim data ke domain LAIN.
    # Ini pola khas pencurian data: tampilan meniru situs resmi, tapi isian
    # penggunanya dikirim ke server milik penipu.
    domain_ini = _domain_dari(url_akhir)
    forms = sup.find_all("form")
    h["jumlah_form"] = len(forms)

    for f in forms:
        aksi = (f.get("action") or "").strip()
        if aksi.startswith(("http://", "https://")):
            tujuan = _domain_dari(aksi)
            if tujuan and domain_ini and tujuan != domain_ini:
                h["form_kirim_ke_domain_lain"] = True
                h["tujuan_form_asing"] = tujuan
                break

    # --- Kata kunci di teks yang benar-benar terlihat pengguna
    teks = sup.get_text(" ", strip=True).lower()[:200_000]

    h["kata_kredensial_di_halaman"] = sum(1 for k in KATA_KREDENSIAL if k in teks)
    kena_judi = [k for k in JUDOL_KEYWORDS if k in teks]
    h["kata_judi_di_halaman"] = len(kena_judi)
    h["kata_judi_kuat_di_halaman"] = sum(1 for k in kena_judi if k in JUDOL_KEYWORDS_KUAT)

    # --- Merek yang disebut di halaman TAPI domainnya bukan milik merek itu
    #
    # Pencocokannya HARUS per kata utuh, bukan sekadar "ada di dalam teks".
    # Merek pendek seperti "bsi", "bca", dan "ovo" sangat mudah nyangkut di
    # tengah kata lain. Terbukti saat pengujian: halaman Tokopedia dituduh
    # menyebut "bsi" padahal itu cuma potongan dari kata lain di halamannya.
    # Kesalahan seperti ini merugikan pemilik situs yang tidak bersalah.
    for merek, resmi in BRANDS.items():
        if domain_ini == resmi:
            continue
        if re.search(rf"(?<![a-z0-9]){re.escape(merek)}(?![a-z0-9])", teks):
            h["merek_disebut_di_halaman"] = merek
            break

    # --- iframe tersembunyi: menyembunyikan halaman lain di balik tampilan
    tersembunyi = 0
    for f in sup.find_all("iframe"):
        gaya = (f.get("style") or "").lower().replace(" ", "")
        if ("display:none" in gaya or "visibility:hidden" in gaya
                or f.get("hidden") is not None
                or str(f.get("width")).strip() in ("0", "0px")):
            tersembunyi += 1
    h["iframe_tersembunyi"] = tersembunyi

    # --- JavaScript yang sengaja diacak
    skrip = " ".join(s.get_text() or "" for s in sup.find_all("script"))[:300_000]
    h["js_teracak"] = any(p.search(skrip) for p in POLA_JS_TERACAK)


# ============================================================
# FUNGSI UTAMA
# ============================================================

def analisis_mendalam(url: str,
                      cache_domain: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Periksa sebuah alamat sampai ke dalamnya.

    Tiap tahap berdiri sendiri: kalau WHOIS gagal, pembacaan halaman tetap
    jalan. Kegagalan dicatat di kunci 'kegagalan' supaya bisa dijelaskan
    ke pengguna, bukan disembunyikan seolah tidak ada masalah.

    Perkiraan waktu 2-8 detik, jauh lebih lambat daripada analisis nama
    domain (0,1 detik). Itu harga yang harus dibayar untuk BUKTI.
    """
    h = _hasil_kosong()

    url_rapi = normalisasi_url(url)
    if not url_rapi:
        h["kegagalan"].append("Alamat kosong")
        return h

    from urllib.parse import urlparse
    hostname = (urlparse(url_rapi).hostname or "").lower()
    domain = _domain_dari(url_rapi)

    # Penjagaan SSRF dijalankan PALING AWAL, sebelum pemeriksaan nama host.
    #
    # Urutannya sempat terbalik, dan akibatnya "file:///C:/Windows/win.ini"
    # ditolak dengan pesan "Nama host tidak terbaca" - benar hasilnya, tapi
    # alasannya menyesatkan. Alamat itu ditolak karena skemanya memang
    # terlarang, bukan karena namanya salah tulis.
    #
    # Kalau hanya pengambilan halaman yang dijaga, tahap DNS dan SSL tetap
    # membuka koneksi ke alamat internal - dan dari situ saja penyerang
    # sudah bisa menyimpulkan layanan apa yang hidup di jaringan dalam,
    # berdasarkan mana yang menjawab dan mana yang tidak.
    aman, alasan = aman_dibuka(url_rapi)
    if not aman:
        h["kegagalan"].append(f"Tidak diperiksa demi keamanan: {alasan}")
        return h

    if not hostname:
        h["kegagalan"].append("Nama host tidak terbaca")
        return h

    # Kalau hasil pemeriksaan domain sudah pernah disimpan, pakai ulang.
    #
    # Hanya bagian STABIL yang dilewati: umur domain, negara, registrar,
    # sertifikat. Isi halaman TIDAK pernah dilewati dan selalu diambil segar,
    # karena halaman phishing bisa berubah dalam hitungan jam - menyajikan
    # isi halaman basi justru lebih berbahaya daripada tidak menyimpan
    # sama sekali.
    if cache_domain:
        h.update(cache_domain)
        h["dari_cache"] = True
    else:
        h["dari_cache"] = False
        _periksa_whois(domain or hostname, h)
        _periksa_jaringan(hostname, h)
        _periksa_ssl(hostname, h)

    html = _ambil_halaman(url_rapi, h)
    if html:
        _baca_isi_halaman(html, h.get("url_akhir") or url_rapi, h)

    return h


if __name__ == "__main__":
    import json
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else "https://github.com"
    print(f"Memeriksa {target} ...\n")
    print(json.dumps(analisis_mendalam(target), indent=2, ensure_ascii=False))
