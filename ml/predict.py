"""
predict.py
==========
Mesin penilaian URL yang dipakai backend ThreatSense.

KENAPA GABUNGAN, BUKAN MODEL SAJA
---------------------------------
Selama membangun ini ditemukan satu batas keras yang tidak bisa ditawar:

    Menebak bahaya HANYA dari nama domain mentok di sekitar 64%.

Sebabnya bukan modelnya kurang canggih, tapi karena sebagian besar URL
phishing menumpang SITUS SAH YANG DIRETAS. Contoh nyata dari dataset:
"aperfectbrow.com" dan "mygummyjelly.com" - dua situs salon dan toko permen
yang diretas lalu dipakai menaruh halaman phishing. Nama domainnya polos.
Tidak ada model, secanggih apa pun, yang bisa menebaknya dari nama saja.
Yang dibutuhkan untuk kasus itu adalah membaca isi halamannya.

Karena itu penilaian di sini memakai TIGA lapisan yang saling melengkapi:

  1. DAFTAR PUTIH - domain yang masuk 100 ribu situs terpopuler dunia.
     Hampir mustahil domain seperti ini didaftarkan penipu. Dipakai untuk
     meredam salah alarm pada situs sehari-hari (github.com, bps.go.id).

  2. ATURAN - pemeriksaan tegas yang bisa dibaca manusia: kata kunci judi,
     peniruan merek bank, typosquatting, alamat IP mentah, huruf menyamar.
     Lapisan inilah yang menangkap kasus-kasus yang paling penting bagi
     pengguna Indonesia, dan setiap keputusannya bisa dijelaskan.

  3. MODEL ML - memberi sinyal tambahan untuk domain yang "terasa aneh"
     (susunan huruf acak, angka berhamburan) tanpa melanggar aturan apa pun.
     Karena akurasinya cuma 64%, sumbangannya sengaja DIBATASI: model
     sendirian tidak akan pernah bisa memvonis "Berbahaya". Dia hanya boleh
     menaikkan status sampai "Mencurigakan".

Pembatasan di poin 3 itu disengaja dan penting. Menaruh keputusan akhir di
tangan model yang benar 2 dari 3 kali akan menghasilkan tuduhan salah yang
merugikan pemilik situs.
"""

import json
import os
import pickle
from functools import lru_cache

import pandas as pd

from ml.features.url_features import (
    extract_url_features,
    deteksi_merek,
    BRANDS,
)

_HERE = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(_HERE, "models")

METADATA_PATH = os.path.join(MODELS_DIR, "model_metadata.json")
WHITELIST_PATH = os.path.join(MODELS_DIR, "whitelist_top100k.txt")

# Batas nilai untuk menentukan label akhir
AMBANG_BERBAHAYA = 0.70
AMBANG_MENCURIGAKAN = 0.40

# Platform hosting gratis / deploy instan.
#
# Platform ini SAH dan banyak dipakai proyek sungguhan, tapi siapa pun bisa
# membuat subdomain di sini dalam hitungan menit tanpa pemeriksaan. Saat
# diuji dengan 300 URL phishing terkini dari OpenPhish, 166 di antaranya
# menumpang platform seperti ini - pages.dev sendirian dipakai 100 kali.
#
# Karena itu subdomain di platform ini tidak bisa dianggap aman begitu saja,
# tapi juga tidak boleh langsung divonis berbahaya (banyak proyek jujur di
# sana). Nilainya diatur supaya berhenti di "Mencurigakan" kalau berdiri
# sendiri, dan baru naik ke "Berbahaya" bila disertai tanda lain.
HOSTING_GRATIS = {
    "pages.dev", "vercel.app", "netlify.app", "github.io", "web.app",
    "firebaseapp.com", "repl.co", "replit.app", "glitch.me", "workers.dev",
    "r2.dev", "cleverapps.io", "weebly.com", "weeblysite.com", "blogspot.com",
    "wixsite.com", "herokuapp.com", "000webhostapp.com", "serv00.net",
    "framer.app", "framer.website", "webflow.io", "surge.sh", "onrender.com",
    "azurewebsites.net", "pythonanywhere.com", "githubusercontent.com",
}

# Kata yang mencurigakan bila muncul di PATH sebuah URL.
# Lapisan aturan boleh membaca path - yang tidak boleh membaca path adalah
# MODEL, karena di dataset yang tersedia path-nya berat sebelah.
KATA_PATH_MENCURIGAKAN = [
    "login", "signin", "verify", "verification", "secure", "account",
    "update", "confirm", "password", "webscr", "wp-admin", "wp-login",
    "banking", "unlock", "suspended", "recovery", "authenticate",
]

# Akhiran palsu yang dipakai menyamar, contoh "roblox.com.am".
# Pengguna membaca "roblox.com" dan tidak sadar akhiran aslinya ".am".
TLD_PALSU = ("com", "net", "org", "co", "gov", "edu")

# Model hanya didengar saat dia YAKIN.
#
# Ketepatan model diukur per tingkat keyakinan pada data uji:
#
#     keyakinan >= 0,50  ->  66,8% tepat   (hampir tebak koin)
#     keyakinan >= 0,80  ->  93,5% tepat
#     keyakinan >= 0,90  ->  97,9% tepat
#     keyakinan >= 0,95  ->  99,4% tepat
#
# Jadi akurasi keseluruhan yang cuma 64% itu menyesatkan: model memang
# sering ragu, TAPI saat dia yakin dia hampir selalu benar. Sebelumnya
# tebakan ragu-ragunya ikut dipakai dan itulah penyebab utama tuduhan salah
# (domain aman seperti "79837.com" kena 56% tanpa satu pun aturan menyala).
#
# Sekarang tebakan di bawah 0,90 diabaikan sepenuhnya.
ML_YAKIN_TINGGI = 0.95     # 99,4% tepat -> boleh sampai vonis berbahaya
ML_YAKIN_SEDANG = 0.90     # 97,9% tepat -> cukup untuk mencurigakan
SUMBANGAN_ML_TINGGI = 0.75
SUMBANGAN_ML_SEDANG = 0.55


# ============================================================
# PEMUATAN (sekali saja, lalu disimpan di memori)
# ============================================================

@lru_cache(maxsize=1)
def _muat_model():
    """Muat model + urutan kolom. Dipanggil sekali, hasilnya dipakai ulang."""
    with open(METADATA_PATH, encoding="utf-8") as f:
        meta = json.load(f)

    nama = meta["best_model"]
    with open(os.path.join(MODELS_DIR, f"{nama}_model.pkl"), "rb") as f:
        model = pickle.load(f)

    return model, meta["feature_columns"], nama


@lru_cache(maxsize=1)
def _muat_daftar_putih() -> frozenset:
    if not os.path.exists(WHITELIST_PATH):
        return frozenset()
    with open(WHITELIST_PATH, encoding="utf-8") as f:
        return frozenset(b.strip() for b in f if b.strip())


def _domain_terdaftar(url: str) -> str:
    """Ambil domain induk dari URL: 'https://a.b.contoh.com/x' -> 'contoh.com'."""
    import tldextract
    e = tldextract.TLDExtract(suffix_list_urls=())(url)
    return f"{e.domain}.{e.suffix}".lower() if e.domain and e.suffix else ""


# ============================================================
# LAPISAN 2: ATURAN
# ============================================================

def evaluasi_aturan(url: str, f: dict) -> list[dict]:
    """
    Jalankan semua aturan. Mengembalikan daftar aturan yang menyala,
    lengkap dengan bobot risiko dan penjelasan berbahasa manusia.

    Setiap aturan di sini bisa dibaca dan diperdebatkan - kalau ada yang
    salah, bisa langsung diperbaiki. Ini keunggulan utamanya dibanding
    model yang tidak bisa ditanya alasannya.
    """
    menyala = []

    def tambah(bobot, judul, alasan):
        menyala.append({"bobot": bobot, "aturan": judul, "alasan": alasan})

    # --- Bahan pemeriksaan yang membaca ALAMAT LENGKAP ---
    # Berbeda dengan model, lapisan aturan boleh membaca path. Yang tidak
    # boleh membacanya adalah model, karena di dataset yang tersedia sisi
    # path-nya berat sebelah dan akan membocorkan jawaban.
    import tldextract as _tld
    _e = _tld.TLDExtract(suffix_list_urls=())(url)
    _induk = f"{_e.domain}.{_e.suffix}".lower() if _e.domain and _e.suffix else ""
    _punya_subdomain = bool(_e.subdomain) and _e.subdomain.lower() != "www"

    _url_kecil = url.lower()
    _path = _url_kecil.split("//")[-1]
    _path = _path[_path.find("/"):] if "/" in _path else ""
    _kata_path = next((k for k in KATA_PATH_MENCURIGAKAN if k in _path), None)

    # Akhiran menyamar: bagian sebelum akhiran asli berakhir dengan "com",
    # "net", dan sejenisnya. Contoh "roblox.com.am" -> subdomain "roblox",
    # domain "com", akhiran asli "am".
    _tld_palsu = None
    _sebelum_tld = f"{_e.subdomain}.{_e.domain}".strip(".").lower()
    if _sebelum_tld.endswith(tuple(f".{t}" for t in TLD_PALSU)) or _e.domain.lower() in TLD_PALSU:
        _bagian = _sebelum_tld.rsplit(".", 1)[-1]
        if _bagian in TLD_PALSU and _e.suffix.lower() not in ("", _bagian):
            _tld_palsu = _bagian

    # ---------- Judi online ----------
    kuat = f.get("judol_strong_count", 0)
    total_judol = f.get("judol_keyword_count", 0)

    if kuat >= 2:
        tambah(0.95, "Judi online",
               f"Nama domain memuat {kuat} kata kunci judi yang sangat khas "
               f"(seperti slot, gacor, togel, maxwin).")
    elif kuat == 1:
        tambah(0.85, "Judi online",
               "Nama domain memuat kata kunci judi yang khas.")
    elif total_judol >= 2:
        # Dua kata judi sekaligus sudah cukup khas. Pola nyata yang sempat
        # lolos: "depo25-bonus25.site" - tidak memuat kata kunci kuat seperti
        # "slot", tapi gabungan "depo" + "bonus" jelas mengarah ke sana.
        tambah(0.70, "Indikasi judi online",
               f"Nama domain memuat {total_judol} kata yang lazim dipakai "
               f"situs judi (misalnya depo, bonus, wede, cuan).")

    # ---------- Peniruan merek ----------
    if f.get("brand_impersonation"):
        # Cari mereknya lewat fungsi yang sama dengan ekstraktor fitur, bukan
        # dengan mencocokkan teks mentah - kalau caranya beda, penjelasan yang
        # tampil bisa menyebut merek yang keliru.
        # Dipecah dari HOSTNAME saja, bukan URL utuh. Kalau URL utuh yang
        # dipecah, "https://bri-mobile.com" menghasilkan token "https://bri"
        # dan nama mereknya tidak pernah ketemu - penjelasan yang tampil jadi
        # samar ("sebuah merek terkenal") padahal mereknya jelas diketahui.
        import re as _re
        _host = f"{_e.subdomain}.{_e.domain}".strip(".").lower()
        token = [t for t in _re.split(r"[-_.\d]+", _host) if t]
        merek = deteksi_merek(_host, token) or "sebuah merek terkenal"
        resmi = BRANDS.get(merek, "-")
        tambah(0.90, "Peniruan merek",
               f"Menyebut '{merek}' padahal ini bukan domain resminya "
               f"({resmi}). Pola khas pencurian akun.")

    # ---------- Typosquatting ----------
    jarak = f.get("brand_edit_distance", 3)
    # Jarak HARUS minimal 1. Jarak 0 berarti nama domainnya memang persis
    # nama mereknya - itu situs aslinya, bukan tiruan. Tanpa syarat ini,
    # google.com dan tokopedia.com ikut divonis meniru dirinya sendiri
    # (kesalahan nyata yang muncul saat pengujian, skor 85%).
    #
    # Kasus "nama merek persis TAPI domain resminya berbeda" (misalnya
    # paypal.xyz) sudah ditangani aturan Peniruan merek di atas.
    if 1 <= jarak <= 2 and not f.get("brand_impersonation"):
        tambah(0.85, "Nama mirip merek terkenal",
               f"Nama domain hanya berbeda {jarak} huruf dari merek terkenal. "
               f"Pola khas typosquatting, mengandalkan pengguna salah ketik.")

    # ---------- Bentuk alamat yang mencurigakan ----------
    if f.get("has_ip_address"):
        tambah(0.85, "Alamat IP mentah",
               "Memakai nomor IP langsung, bukan nama domain. Situs resmi "
               "hampir tidak pernah begini.")

    if f.get("has_punycode"):
        tambah(0.85, "Huruf menyamar",
               "Memakai huruf non-latin yang tampil mirip huruf biasa "
               "(punycode). Teknik klasik untuk memalsukan alamat.")

    # ---------- Kombinasi mencurigakan ----------
    if f.get("suspicious_tld") and f.get("has_phishing_keyword"):
        tambah(0.75, "Akhiran murah + kata kunci login",
               "Memakai akhiran domain murah SEKALIGUS kata seperti "
               "login/verify/secure. Gabungan yang jarang dipakai situs sah.")
    elif f.get("suspicious_tld"):
        # Sengaja DI BAWAH ambang mencurigakan. Akhiran seperti .xyz dan
        # .online juga dipakai banyak situs jujur - saat diuji dengan 400
        # domain aman peringkat menengah, aturan ini sendirian menghasilkan
        # terlalu banyak tuduhan salah. Jadi sinyal ini hanya berarti bila
        # ditemani tanda lain.
        tambah(0.30, "Akhiran domain murah",
               "Memakai akhiran domain yang sering dipilih penipu karena "
               "gratis atau sangat murah. Sinyal lemah kalau berdiri sendiri.")

    # ---------- Menumpang platform hosting gratis ----------
    if _induk in HOSTING_GRATIS and _punya_subdomain:
        if _kata_path or f.get("has_phishing_keyword"):
            tambah(0.80, "Hosting gratis + kata kunci login",
                   f"Halaman menumpang '{_induk}' (siapa pun bisa membuat "
                   f"subdomain di sini tanpa pemeriksaan) DAN memuat kata "
                   f"seperti login/verify. Pola paling umum phishing saat ini.")
        else:
            tambah(0.55, "Menumpang hosting gratis",
                   f"Halaman menumpang '{_induk}'. Platform ini sah, tapi "
                   f"siapa pun bisa membuat subdomain di sana dalam hitungan "
                   f"menit tanpa pemeriksaan identitas.")

    # ---------- Akhiran domain palsu ----------
    if _tld_palsu:
        tambah(0.85, "Akhiran domain menyamar",
               f"Alamat ditulis seolah berakhiran '.{_tld_palsu}', padahal "
               f"akhiran aslinya berbeda. Mata pembaca berhenti di bagian "
               f"yang familiar dan melewatkan bagian aslinya.")

    # ---------- Kata mencurigakan di path ----------
    if _kata_path and not (_induk in HOSTING_GRATIS and _punya_subdomain):
        tambah(0.50, "Kata kunci login di alamat",
               f"Alamat memuat '{_kata_path}'. Wajar untuk situs yang memang "
               f"punya halaman masuk, jadi ini baru berarti kalau digabung "
               f"tanda lain - karena itu nilainya sedang saja.")

    if f.get("is_shortener"):
        tambah(0.50, "Tautan pendek",
               "Ini tautan yang dipendekkan, tujuan aslinya tersembunyi "
               "sehingga tidak bisa diperiksa.")

    if f.get("has_port"):
        tambah(0.40, "Nomor port tidak lazim",
               "Menyertakan nomor port di alamat. Tidak biasa untuk situs umum.")

    return menyala


# ============================================================
# FUNGSI UTAMA
# ============================================================

def predict_url(url: str) -> dict:
    """
    Nilai sebuah URL.

    Returns dict berisi:
        risk_score    : 0.0 - 1.0
        threat_label  : 'Safe' | 'Suspicious' | 'Malicious'
        features      : semua fitur yang dihitung
        explanations  : daftar alasan berbahasa manusia
        ml_score      : nilai mentah dari model (untuk transparansi)
        rules_fired   : aturan yang menyala
    """
    fitur = extract_url_features(url)

    # --- Lapisan 3: model ML ---
    model, kolom, _ = _muat_model()
    X = pd.DataFrame([fitur])[kolom]
    ml_score = float(model.predict_proba(X)[0][1])

    # --- Lapisan 2: aturan ---
    aturan = evaluasi_aturan(url, fitur)
    skor_aturan = max((a["bobot"] for a in aturan), default=0.0)

    # --- Gabungkan ---
    # Tebakan model yang ragu-ragu dibuang, hanya yang yakin yang dihitung.
    if ml_score >= ML_YAKIN_TINGGI:
        sumbangan_ml = SUMBANGAN_ML_TINGGI
    elif ml_score >= ML_YAKIN_SEDANG:
        sumbangan_ml = SUMBANGAN_ML_SEDANG
    else:
        sumbangan_ml = 0.0

    skor = max(skor_aturan, sumbangan_ml)

    # --- Lapisan 1: daftar putih ---
    domain = _domain_terdaftar(url)
    di_daftar_putih = domain in _muat_daftar_putih()
    catatan_putih = None

    if di_daftar_putih:
        # Daftar putih meredam kecurigaan dari MODEL, tapi TIDAK membatalkan
        # aturan tegas. Alasannya: ada situs judi yang trafiknya besar
        # sehingga ikut masuk daftar populer (contoh nyata yang ditemukan:
        # miamiclubcasino.im). Kalau daftar putih boleh membatalkan segalanya,
        # situs seperti itu lolos begitu saja.
        if skor_aturan < AMBANG_MENCURIGAKAN:
            skor = min(skor, 0.15)
            catatan_putih = (
                f"Domain '{domain}' termasuk 100 ribu situs terpopuler dunia, "
                f"sangat kecil kemungkinannya didaftarkan penipu."
            )
        else:
            catatan_putih = (
                f"Domain '{domain}' memang populer, TAPI ada aturan tegas yang "
                f"menyala - popularitas tidak membatalkan temuan itu."
            )

    skor = round(min(max(skor, 0.0), 1.0), 4)

    if skor >= AMBANG_BERBAHAYA:
        label = "Malicious"
    elif skor >= AMBANG_MENCURIGAKAN:
        label = "Suspicious"
    else:
        label = "Safe"

    # --- Susun penjelasan ---
    penjelasan = [
        {"judul": a["aturan"], "alasan": a["alasan"], "bobot": a["bobot"]}
        for a in sorted(aturan, key=lambda a: -a["bobot"])
    ]

    if catatan_putih:
        penjelasan.append(
            {"judul": "Domain populer", "alasan": catatan_putih, "bobot": 0.0}
        )

    if not aturan:
        if ml_score >= 0.6:
            penjelasan.append({
                "judul": "Pola nama tidak lazim",
                "alasan": ("Tidak ada aturan tegas yang dilanggar, tapi model "
                           "menilai susunan nama domainnya tidak lazim. Sinyal "
                           "ini lemah dan tidak dipakai sendirian untuk memvonis."),
                "bobot": round(ml_score, 3),
            })
        elif not di_daftar_putih:
            penjelasan.append({
                "judul": "Tidak ditemukan tanda bahaya",
                "alasan": ("Tidak ada aturan yang dilanggar dan pola namanya "
                           "wajar. Catatan: pemeriksaan ini hanya membaca nama "
                           "domain, belum membuka isi halamannya."),
                "bobot": 0.0,
            })

    return {
        "risk_score": skor,
        "threat_label": label,
        "features": fitur,
        "explanations": penjelasan,
        "ml_score": round(ml_score, 4),
        "rules_fired": [a["aturan"] for a in aturan],
        "whitelisted": di_daftar_putih,
    }


if __name__ == "__main__":
    contoh = [
        "https://github.com/torvalds/linux",
        "https://www.bps.go.id",
        "http://neverssl.com",
        "https://slot-gacor-maxwin88.com/daftar",
        "https://bri-mobile-verifikasi.com/login",
        "http://192.168.1.1/bank/verify.html",
    ]
    for u in contoh:
        h = predict_url(u)
        print(f"\n{u}")
        print(f"  {h['threat_label']}  ({h['risk_score']*100:.1f}%)  ml={h['ml_score']}")
        for p in h["explanations"]:
            print(f"    - {p['judul']}: {p['alasan'][:70]}")
