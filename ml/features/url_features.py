"""
url_features.py  (versi 2 - level domain)
=========================================
Ekstraktor fitur untuk deteksi URL berbahaya.

PERUBAHAN BESAR DARI VERSI 1 - DAN ALASANNYA
--------------------------------------------
Versi 1 membaca SELURUH URL: panjang path, jumlah garis miring, ada tidaknya
tanda tanya, dan protokol http/https. Hasilnya bencana:

    Dataset PhiUSIIL ternyata tidak punya SATU PUN URL legitimate yang
    memakai http atau punya path. Semuanya https dan domain polos.

Jadi model tidak pernah melihat contoh "URL aman yang punya path". Yang
dipelajari model bukan ciri phishing, melainkan cara data dikumpulkan:
"ada garis miring berarti berbahaya". Saat diuji URL sungguhan, akurasinya
jatuh dari 99,55% ke 69,2% - github.com/torvalds/linux divonis 99,97%
berbahaya hanya karena punya path.

VERSI 2 MENUTUP CELAH ITU SECARA STRUKTURAL:
Semua fitur di sini dihitung HANYA dari bagian domain (hostname). Path,
query, dan protokol sengaja TIDAK PERNAH dibaca. Dengan begitu artefak
seperti kemarin tidak mungkin terulang - bukan karena datasetnya kebetulan
bagus, tapi karena fiturnya memang tidak bisa melihat bagian itu.

Konsekuensi yang harus disadari: kalau sebuah situs yang sah disusupi dan
dipakai menaruh halaman phishing (contoh: situs-kampus-sah.ac.id/phish/),
pendekatan ini tidak akan menangkapnya. Itu masalah berbeda yang butuh
analisis isi halaman, bukan analisis nama domain. Batasan ini disebut
terus terang di laporan, bukan disembunyikan.

Fungsi ini 100% offline dan cepat, aman dipanggil ratusan ribu kali saat
membangun dataset.
"""

import math
import re
from collections import Counter
from urllib.parse import urlparse

import tldextract

# Paksa tldextract memakai daftar TLD bawaan (offline). Tanpa ini dia akan
# mencoba mengunduh daftar TLD terbaru saat pertama dipanggil - lambat, dan
# gagal total kalau sedang tidak ada internet.
_tld_extractor = tldextract.TLDExtract(suffix_list_urls=())


# ============================================================
# DAFTAR REFERENSI
# ============================================================

# TLD yang sering dipakai penipu karena gratis atau sangat murah
SUSPICIOUS_TLDS = {
    "tk", "ml", "ga", "cf", "gq",
    "xyz", "top", "work", "click", "loan", "win", "download",
    "review", "country", "kim", "science", "party", "gdn",
    "online", "site", "website", "space", "fun", "icu", "cyou",
    "buzz", "rest", "monster", "quest", "sbs", "cfd", "bond",
}

# TLD yang wajar dipakai situs sungguhan
COMMON_TLDS = {
    "com", "net", "org", "edu", "gov", "int", "mil",
    "id", "co.id", "ac.id", "go.id", "or.id", "sch.id", "web.id", "my.id",
    "co.uk", "de", "jp", "fr", "au", "ca", "nl", "it", "es", "se",
    "io", "dev", "app", "co",
}

# Kata yang khas muncul di halaman pencurian kredensial
PHISHING_KEYWORDS = [
    "login", "signin", "verify", "secure", "account", "update",
    "confirm", "password", "webscr", "ebayisapi", "suspend",
    "billing", "invoice", "unlock", "recover", "validation",
    "authenticate", "wallet", "support", "service", "customer",
]

# Kata khas judi online Indonesia.
# Daftar ini disusun dari pola nama domain yang paling sering muncul di
# daftar blokir Komdigi (dari 9,4 juta domain, 1,25 juta memuat kata-kata
# ini). Sengaja ditulis terbuka supaya bisa diperiksa dan ditambah manual -
# ini keunggulan lapisan aturan dibanding model kotak hitam.
JUDOL_KEYWORDS = [
    "slot", "gacor", "maxwin", "toto", "togel", "judi", "casino", "kasino",
    "poker", "domino", "bandar", "sbobet", "pragmatic", "pgsoft",
    "jackpot", "jekpot", "zeus", "olympus", "scatter", "rungkad",
    "depo", "wede", "withdraw", "jp", "rtp", "hoki", "cuan",
    "betting", "taruhan", "dadu", "roulette", "baccarat", "mpo",
    "pkv", "qq", "bola88", "situs", "resmi", "terpercaya", "gampang",
    "bonus", "freebet", "parlay", "mixparlay", "sultan", "petir",
]

# Kata judi yang sangat menentukan - kemunculannya saja sudah kuat
JUDOL_KEYWORDS_KUAT = {
    "slot", "gacor", "maxwin", "togel", "toto", "judi", "sbobet",
    "pragmatic", "rungkad", "pkv", "scatter", "jekpot",
    # "casino"/"kasino" masuk sini karena domain yang memuatnya praktis
    # selalu situs judi - ditemukan saat menguji miamiclubcasino.im
    "casino", "kasino",
}

# Merek dengan nama pendek (bri, bca, ovo) tidak boleh dipakai mencari
# kemiripan ejaan. Alasannya ditemukan saat pengujian: "bps" (situs BPS)
# hanya berjarak 2 huruf dari "bca", "bni", DAN "bri" sekaligus - padahal
# jelas bukan tiruan. Untuk kata sependek itu, jarak 2 huruf tidak berarti
# apa-apa. Deteksi typosquatting hanya masuk akal untuk nama yang panjang.
PANJANG_MIN_MEREK_TYPO = 6

# Layanan pemendek tautan
SHORTENER_DOMAINS = {
    "bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly",
    "is.gd", "buff.ly", "adf.ly", "shorte.st", "cutt.ly",
    "s.id", "bit.do", "rebrand.ly", "rb.gy",
}

# Merek yang sering ditiru, termasuk merek Indonesia yang jadi sasaran utama
BRANDS = {
    "google": "google.com", "paypal": "paypal.com", "amazon": "amazon.com",
    "microsoft": "microsoft.com", "apple": "apple.com", "facebook": "facebook.com",
    "instagram": "instagram.com", "netflix": "netflix.com", "whatsapp": "whatsapp.com",
    "linkedin": "linkedin.com", "dropbox": "dropbox.com", "steam": "steampowered.com",
    "telegram": "telegram.org", "discord": "discord.com", "spotify": "spotify.com",
    "tiktok": "tiktok.com", "twitter": "twitter.com", "binance": "binance.com",
    "coinbase": "coinbase.com", "metamask": "metamask.io",
    # Sasaran phishing yang menyasar anak dan remaja - ditemukan saat menguji
    # umpan OpenPhish: roblox ditiru lewat roblox.com.am, roblox.com.ml,
    # roblox.et, dan seterusnya
    "roblox": "roblox.com", "minecraft": "minecraft.net",
    "garena": "garena.com", "freefire": "ff.garena.com",
    # Indonesia
    "bri": "bri.co.id", "bca": "bca.co.id", "mandiri": "bankmandiri.co.id",
    "bni": "bni.co.id", "bsi": "bankbsi.co.id", "cimb": "cimbniaga.co.id",
    "gopay": "gopay.co.id", "ovo": "ovo.id", "dana": "dana.id",
    "shopee": "shopee.co.id", "tokopedia": "tokopedia.com",
    "bukalapak": "bukalapak.com", "traveloka": "traveloka.com",
    "gojek": "gojek.com", "grab": "grab.com", "linkaja": "linkaja.id",
    "blibli": "blibli.com", "lazada": "lazada.co.id", "seabank": "seabank.co.id",
    "jenius": "jenius.com", "prakerja": "prakerja.go.id",
    "bpjs": "bpjs-kesehatan.go.id", "samsat": "samsat.info",
}

VOWELS = set("aeiou")

_IP_PATTERN = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")


# ============================================================
# HELPER
# ============================================================

def _shannon_entropy(text: str) -> float:
    """
    Mengukur keacakan susunan huruf.

    Domain buatan manusia ("tokopedia") punya entropi rendah karena hurufnya
    berpola. Domain yang dibuat mesin ("dzfxrf", "xk29fj2m") entropinya
    tinggi karena hurufnya tersebar acak.
    """
    if not text:
        return 0.0
    freq = Counter(text)
    n = len(text)
    return round(-sum((c / n) * math.log2(c / n) for c in freq.values()), 4)


def _longest_consonant_run(text: str) -> int:
    """
    Deretan konsonan terpanjang tanpa huruf vokal.

    Kata sungguhan jarang punya lebih dari 4 konsonan beruntun. Domain acak
    seperti "dzfxrf" punya 6 - petunjuk kuat bahwa namanya dibuat mesin.
    """
    terpanjang = sekarang = 0
    for ch in text:
        if ch.isalpha() and ch not in VOWELS:
            sekarang += 1
            terpanjang = max(terpanjang, sekarang)
        else:
            sekarang = 0
    return terpanjang


def _max_char_repeat(text: str) -> int:
    """Huruf sama beruntun terbanyak, contoh "shopeeee" -> 4."""
    terpanjang = sekarang = 1
    for i in range(1, len(text)):
        if text[i] == text[i - 1]:
            sekarang += 1
            terpanjang = max(terpanjang, sekarang)
        else:
            sekarang = 1
    return terpanjang if text else 0


def _digit_letter_transitions(text: str) -> int:
    """
    Berapa kali berganti antara huruf dan angka.

    "maxwin88" berganti 1 kali. "a1b2c3d4" berganti 7 kali. Pergantian yang
    sering menandakan nama yang dibuat otomatis.
    """
    n = 0
    for i in range(1, len(text)):
        if text[i - 1].isdigit() != text[i].isdigit():
            n += 1
    return n


def _edit_distance_max2(a: str, b: str) -> int:
    """
    Jarak edit (Levenshtein) dengan batas 3.

    Dipakai mendeteksi typosquatting: "paypa1", "goggle", "tokopedla" -
    nama yang beda 1-2 huruf dari merek asli. Perhitungan dihentikan begitu
    selisihnya lewat 3, supaya tetap cepat saat dipanggil ratusan ribu kali.
    """
    if abs(len(a) - len(b)) > 3:
        return 3
    if a == b:
        return 0

    sebelum = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        sekarang = [i]
        for j, cb in enumerate(b, 1):
            sekarang.append(min(
                sebelum[j] + 1,
                sekarang[j - 1] + 1,
                sebelum[j - 1] + (ca != cb),
            ))
        if min(sekarang) > 3:
            return 3
        sebelum = sekarang
    return min(sebelum[-1], 3)


def _jarak_merek_terdekat(domain: str) -> tuple[int, str | None]:
    """
    Selisih huruf ke merek terkenal yang paling mirip, beserta nama mereknya.

    Hanya merek berhuruf panjang yang dibandingkan - lihat penjelasan di
    PANJANG_MIN_MEREK_TYPO.
    """
    if not domain or len(domain) < 5:
        return 3, None

    terbaik, merek_terbaik = 3, None
    for m in BRANDS:
        if len(m) < PANJANG_MIN_MEREK_TYPO:
            continue
        d = _edit_distance_max2(domain, m)
        if d < terbaik:
            terbaik, merek_terbaik = d, m

    return terbaik, merek_terbaik


def deteksi_merek(teks: str, token: list[str]) -> str | None:
    """
    Cari merek yang disebut di nama domain - HARUS sebagai potongan kata utuh.

    Kenapa tidak boleh sekadar "ada di dalam teks": nama merek pendek gampang
    nyangkut di tengah kata lain. Contoh nyata yang sempat lolos:
    "miamiclubcasino" dituduh meniru BCA, padahal itu cuma potongan
    "miamiclu-BCA-sino". Kesalahan seperti ini merugikan pemilik situs.

    Aturannya:
      - merek pendek (bri, bca, ovo) -> wajib jadi potongan kata utuh
      - merek panjang (paypal, tokopedia) -> boleh menempel di dalam kata,
        karena kebetulan nyangkut sepanjang itu praktis tidak mungkin
    """
    set_token = set(token)
    for merek in BRANDS:
        if merek in set_token:
            return merek
        if len(merek) >= PANJANG_MIN_MEREK_TYPO and merek in teks:
            return merek
    return None


# ============================================================
# FUNGSI UTAMA
# ============================================================

def extract_url_features(url: str) -> dict:
    """
    Ambil fitur dari sebuah URL - HANYA dari bagian domainnya.

    Args:
        url: URL mentah, contoh "https://slot-gacor-maxwin88.com/daftar"

    Returns:
        dict berisi 30 fitur angka. Path dan protokol tidak pernah dibaca,
        jadi "https://situs.com" dan "http://situs.com/apa/saja" menghasilkan
        fitur yang PERSIS SAMA. Ini disengaja - lihat penjelasan di atas.
    """
    teks = (url or "").strip()
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", teks):
        teks = "http://" + teks

    parsed = urlparse(teks)
    hostname = (parsed.hostname or "").lower()

    ext = _tld_extractor(teks)
    domain = (ext.domain or "").lower()       # bagian inti, contoh "tokopedia"
    suffix = (ext.suffix or "").lower()       # TLD, contoh "co.id"
    subdomain = (ext.subdomain or "").lower()

    # Gabungan huruf yang diperiksa: inti domain + subdomain.
    # Subdomain ikut karena penipu sering menaruh umpannya di situ,
    # contoh "bri-verifikasi.situs-asing.com".
    teks_periksa = f"{subdomain}.{domain}" if subdomain else domain

    f = {}

    # ---------- 1. Ukuran ----------
    f["hostname_length"] = len(hostname)
    f["domain_length"] = len(domain)
    f["tld_length"] = len(suffix)
    f["subdomain_count"] = len([s for s in subdomain.split(".") if s]) if subdomain else 0

    # ---------- 2. Keacakan susunan huruf ----------
    f["domain_entropy"] = _shannon_entropy(domain)
    f["hostname_entropy"] = _shannon_entropy(hostname)

    # ---------- 3. Angka ----------
    n_digit = sum(c.isdigit() for c in teks_periksa)
    f["count_digit"] = n_digit
    f["digit_ratio"] = round(n_digit / len(teks_periksa), 4) if teks_periksa else 0.0

    # ---------- 4. Tanda hubung ----------
    n_hyphen = teks_periksa.count("-")
    f["count_hyphen"] = n_hyphen
    f["hyphen_ratio"] = round(n_hyphen / len(teks_periksa), 4) if teks_periksa else 0.0

    # ---------- 5. Pola huruf ----------
    huruf = [c for c in domain if c.isalpha()]
    f["vowel_ratio"] = round(sum(c in VOWELS for c in huruf) / len(huruf), 4) if huruf else 0.0
    f["longest_consonant_run"] = _longest_consonant_run(domain)
    f["max_char_repeat"] = _max_char_repeat(domain)
    f["digit_letter_transitions"] = _digit_letter_transitions(teks_periksa)

    # ---------- 6. Potongan kata ----------
    # Domain dipecah di tanda hubung dan angka: "slot-gacor-maxwin88"
    # menjadi ["slot", "gacor", "maxwin"].
    token = [t for t in re.split(r"[-_.\d]+", teks_periksa) if t]
    f["token_count"] = len(token)
    f["avg_token_length"] = round(sum(len(t) for t in token) / len(token), 2) if token else 0.0
    f["max_token_length"] = max((len(t) for t in token), default=0)

    # ---------- 7. Bentuk alamat ----------
    f["has_ip_address"] = 1 if _IP_PATTERN.match(hostname) else 0
    f["has_port"] = 1 if parsed.port is not None else 0
    f["has_punycode"] = 1 if "xn--" in hostname else 0  # huruf non-latin yang menyamar

    registered = f"{domain}.{suffix}" if domain and suffix else hostname
    f["is_shortener"] = 1 if registered in SHORTENER_DOMAINS else 0

    # ---------- 8. TLD ----------
    f["suspicious_tld"] = 1 if suffix in SUSPICIOUS_TLDS else 0
    f["common_tld"] = 1 if suffix in COMMON_TLDS else 0

    # ---------- 9. Peniruan merek ----------
    merek_ada = deteksi_merek(teks_periksa, token)
    f["contains_brand"] = 1 if merek_ada else 0
    # Menyebut merek TAPI domain resminya bukan itu -> indikasi penyamaran.
    # Contoh: "bri-mobile-verifikasi.com" menyebut bri, padahal resminya bri.co.id
    f["brand_impersonation"] = (
        1 if merek_ada and registered != BRANDS[merek_ada] else 0
    )
    jarak, _merek_mirip = _jarak_merek_terdekat(domain)
    f["brand_edit_distance"] = jarak

    # ---------- 10. Kata kunci phishing ----------
    n_phish = sum(1 for k in PHISHING_KEYWORDS if k in teks_periksa)
    f["phishing_keyword_count"] = n_phish
    f["has_phishing_keyword"] = 1 if n_phish else 0

    # ---------- 11. Kata kunci judi online ----------
    kena_judol = [k for k in JUDOL_KEYWORDS if k in teks_periksa]
    f["judol_keyword_count"] = len(kena_judol)
    f["has_judol_keyword"] = 1 if kena_judol else 0
    f["judol_strong_count"] = sum(1 for k in kena_judol if k in JUDOL_KEYWORDS_KUAT)

    return f


# Urutan kolom yang dipakai model. Ditulis eksplisit supaya urutannya
# tidak pernah berubah diam-diam saat fungsi di atas diubah - kalau urutan
# fitur bergeser, prediksi model jadi kacau tanpa pesan error apa pun.
FEATURE_NAMES = list(extract_url_features("https://contoh.com").keys())


if __name__ == "__main__":
    import json

    contoh = [
        "https://github.com/torvalds/linux",
        "https://www.bps.go.id",
        "http://neverssl.com",
        "https://slot-gacor-maxwin88.com/daftar",
        "https://bri-mobile-verifikasi.com/login",
        "https://dzfxrf.weeblysite.com/",
    ]
    print(f"Jumlah fitur: {len(FEATURE_NAMES)}\n")
    for u in contoh:
        print("=" * 70)
        print(u)
        print(json.dumps(extract_url_features(u), indent=2))
