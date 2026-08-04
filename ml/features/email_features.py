"""
email_features.py
=================
Ekstraktor fitur untuk deteksi email phishing.

PENDEKATAN YANG DIPAKAI - DAN KENAPA BUKAN FINE-TUNING DULU
-----------------------------------------------------------
Rencana awal project ini adalah melatih model bahasa (IndoBERT) untuk
membaca isi email. Itu memang pendekatan yang tepat untuk email, karena
email adalah tulisan panjang berbahasa manusia - beda dengan URL yang cuma
sebaris teks pendek.

Tapi ada syarat yang belum terpenuhi: fine-tuning butuh RIBUAN contoh email
phishing berbahasa Indonesia yang sudah diberi label. Dataset seperti itu
belum ada, dan mengumpulkannya sendiri butuh waktu berminggu-minggu.

Jadi versi pertama ini memakai analisis terstruktur yang tidak perlu data
latih sama sekali. Semua yang diperiksa di sini adalah hal yang bisa
dipastikan benar-salahnya tanpa menebak:

    - Alamat pengirim berbeda dengan alamat balasan?  (bisa dicek pasti)
    - Nama tampilan mengaku bank, tapi alamatnya gmail? (bisa dicek pasti)
    - Tautan tertulis "bri.co.id" tapi mengarah ke tempat lain? (pasti)
    - Ada lampiran .exe menyamar jadi .pdf? (pasti)

Begitu nanti terkumpul cukup contoh email berlabel, model bahasa bisa
DITAMBAHKAN sebagai lapisan baru - persis seperti model URL yang sekarang
melengkapi aturan, bukan menggantikannya.

Fungsi di sini 100% offline dan tidak mengirim isi email ke mana pun.
"""

import re
from email import message_from_string
from email.utils import parseaddr, getaddresses

# ============================================================
# DAFTAR REFERENSI
# ============================================================

# Kata yang memaksa korban bertindak cepat supaya tidak sempat berpikir.
# Ditulis dalam dua bahasa karena email phishing ke pengguna Indonesia
# sering campur - subjeknya Indonesia, isinya template Inggris.
KATA_MENDESAK = [
    # Indonesia
    "segera", "mendesak", "penting", "batas waktu", "kedaluwarsa",
    "diblokir", "dibekukan", "ditangguhkan", "terakhir", "sekarang juga",
    "dalam 24 jam", "akan dihapus", "akan ditutup", "verifikasi sekarang",
    "konfirmasi sekarang", "jangan abaikan", "peringatan terakhir",
    # Inggris
    "urgent", "immediately", "expire", "expired", "suspended", "locked",
    "deadline", "final notice", "act now", "within 24 hours",
    "verify now", "confirm now", "last warning", "account closure",
]

# Kata yang meminta data rahasia. Lembaga resmi TIDAK PERNAH meminta ini
# lewat email.
KATA_MINTA_DATA = [
    # Indonesia
    "kata sandi", "sandi", "pin", "otp", "kode otp", "kode verifikasi",
    "nomor rekening", "nomor kartu", "cvv", "kode cvv", "m-pin",
    "data pribadi", "nik", "ktp", "mother maiden",
    # Inggris
    "password", "credential", "card number", "account number",
    "social security", "security code", "one time password",
]

# Iming-iming hadiah - umpan klasik
KATA_HADIAH = [
    "selamat anda", "anda terpilih", "hadiah", "undian", "menang",
    "gratis", "bonus", "cashback", "saldo", "voucher", "klaim",
    "congratulations", "you won", "prize", "claim your", "free gift",
]

# Lampiran yang bisa langsung menjalankan program di komputer korban
EKSTENSI_BERBAHAYA = {
    "exe", "scr", "com", "pif", "bat", "cmd", "vbs", "vbe", "js", "jse",
    "wsf", "wsh", "msi", "msc", "jar", "ps1", "hta", "cpl", "reg",
    "lnk", "iso", "img", "apk",
}

# Lampiran yang bisa berisi makro/skrip tersembunyi
EKSTENSI_WASPADA = {
    "docm", "xlsm", "pptm", "dotm", "xltm", "xlam", "zip", "rar", "7z",
}

# Layanan email gratis. Bukan tanda bahaya kalau berdiri sendiri, tapi
# menjadi sangat mencurigakan bila nama pengirimnya mengaku lembaga resmi.
EMAIL_GRATIS = {
    "gmail.com", "yahoo.com", "yahoo.co.id", "hotmail.com", "outlook.com",
    "outlook.co.id", "aol.com", "mail.com", "gmx.com", "yandex.com",
    "protonmail.com", "zoho.com", "rocketmail.com", "live.com",
}

# Lembaga yang sering ditiru di email phishing Indonesia.
# Dipakai memeriksa: nama pengirim mengaku salah satu ini, tapi alamat
# emailnya bukan domain resmi mereka.
LEMBAGA_RESMI = {
    "bri": ["bri.co.id", "bankbri.co.id"],
    "bca": ["bca.co.id", "klikbca.com"],
    "mandiri": ["bankmandiri.co.id"],
    "bni": ["bni.co.id"],
    "bsi": ["bankbsi.co.id"],
    "btn": ["btn.co.id"],
    "cimb": ["cimbniaga.co.id"],
    "permata": ["permatabank.com"],
    "danamon": ["danamon.co.id"],
    "ovo": ["ovo.id"],
    "gopay": ["gopay.co.id", "gojek.com"],
    "dana": ["dana.id"],
    "shopee": ["shopee.co.id", "shopee.com"],
    "tokopedia": ["tokopedia.com"],
    "bukalapak": ["bukalapak.com"],
    "lazada": ["lazada.co.id"],
    "grab": ["grab.com"],
    "gojek": ["gojek.com"],
    "telkomsel": ["telkomsel.com", "telkomsel.co.id"],
    "indihome": ["indihome.co.id", "telkom.co.id"],
    "pln": ["pln.co.id"],
    "bpjs": ["bpjs-kesehatan.go.id", "bpjsketenagakerjaan.go.id"],
    "pajak": ["pajak.go.id"],
    "prakerja": ["prakerja.go.id"],
    "paypal": ["paypal.com"],
    "netflix": ["netflix.com"],
    "microsoft": ["microsoft.com", "outlook.com"],
    "google": ["google.com", "gmail.com"],
    "apple": ["apple.com", "icloud.com"],
    "whatsapp": ["whatsapp.com"],
    "instagram": ["instagram.com"],
    "facebook": ["facebook.com", "fb.com"],
}

# Pola tautan di dalam teks
_POLA_URL = re.compile(r"""https?://[^\s<>"'\)\]]+""", re.IGNORECASE)

# Pola tautan HTML: <a href="tujuan">tulisan yang terlihat</a>
_POLA_ANCHOR = re.compile(
    r"""<a\s[^>]*href\s*=\s*["']([^"']+)["'][^>]*>(.*?)</a>""",
    re.IGNORECASE | re.DOTALL,
)

_POLA_TAG = re.compile(r"<[^>]+>")

# Nama berkas yang tertulis sebagai TEKS BIASA di dalam email.
#
# KENAPA PERLU:
# Lampiran seharusnya ditemukan lewat struktur MIME. Tapi struktur itu hilang
# begitu pengguna menyalin-tempel email dari Gmail atau Outlook - yang
# tersisa cuma tulisan nama berkasnya. Padahal itu cara paling umum orang
# memakai alat ini.
#
# Ditemukan saat pengujian: contoh lampiran "invoice_2024.pdf.exe" sama
# sekali tidak terdeteksi karena emailnya bukan MIME sungguhan.
_POLA_NAMA_BERKAS = re.compile(
    r"""[\w\-. ]+\.[a-z0-9]{2,5}(?:\.[a-z0-9]{2,4})?""",
    re.IGNORECASE,
)


# ============================================================
# HELPER
# ============================================================

def _domain_dari_email(alamat: str) -> str:
    """Ambil bagian setelah @ dari sebuah alamat email."""
    if not alamat or "@" not in alamat:
        return ""
    return alamat.rsplit("@", 1)[-1].strip().lower().strip(">")


def _hitung_kata(teks: str, daftar: list[str]) -> list[str]:
    """Kembalikan kata dari daftar yang benar-benar muncul di teks."""
    rendah = teks.lower()
    return [k for k in daftar if k in rendah]


def _buang_tag_html(teks: str) -> str:
    return _POLA_TAG.sub(" ", teks)


def parse_email(mentah: str) -> dict:
    """
    Pisahkan email menjadi bagian-bagiannya.

    Menerima DUA bentuk masukan:
      1. Email mentah lengkap dengan header (From:, To:, Subject:, ...)
      2. Teks biasa hasil salin-tempel dari aplikasi email

    Bentuk kedua sengaja didukung karena pengguna biasa tidak tahu cara
    mengambil header mentah - mereka hanya menyalin isi email yang terlihat.
    Analisis header otomatis dilewati kalau header memang tidak ada.
    """
    punya_header = bool(
        re.search(r"^(from|dari|subject|subjek|to)\s*:", mentah,
                  re.IGNORECASE | re.MULTILINE)
    )

    hasil = {
        "punya_header": punya_header,
        "from_addr": "", "from_name": "", "reply_to": "",
        "return_path": "", "subject": "", "body": mentah,
        "attachments": [],
    }

    if not punya_header:
        return hasil

    try:
        msg = message_from_string(mentah)
    except Exception:
        return hasil

    nama, alamat = parseaddr(msg.get("From", "") or msg.get("Dari", "") or "")
    hasil["from_name"] = (nama or "").strip()
    hasil["from_addr"] = (alamat or "").strip().lower()

    balasan = getaddresses(msg.get_all("Reply-To", []) or [])
    hasil["reply_to"] = balasan[0][1].strip().lower() if balasan else ""

    _, rp = parseaddr(msg.get("Return-Path", "") or "")
    hasil["return_path"] = (rp or "").strip().lower()

    hasil["subject"] = (msg.get("Subject") or msg.get("Subjek") or "").strip()

    # Kumpulkan isi + nama lampiran
    potongan, lampiran = [], []
    if msg.is_multipart():
        for bagian in msg.walk():
            nama_file = bagian.get_filename()
            if nama_file:
                lampiran.append(nama_file)
                continue
            if bagian.get_content_type() in ("text/plain", "text/html"):
                try:
                    potongan.append(
                        bagian.get_payload(decode=True).decode(
                            bagian.get_content_charset() or "utf-8", "replace"
                        )
                    )
                except Exception:
                    potongan.append(str(bagian.get_payload()))
    else:
        try:
            isi = msg.get_payload(decode=True)
            potongan.append(
                isi.decode(msg.get_content_charset() or "utf-8", "replace")
                if isi else str(msg.get_payload())
            )
        except Exception:
            potongan.append(str(msg.get_payload()))

    hasil["body"] = "\n".join(potongan) if potongan else mentah
    hasil["attachments"] = lampiran
    return hasil


def ambil_tautan(teks: str) -> list[str]:
    """Ambil semua alamat web yang muncul di dalam teks."""
    urls = _POLA_URL.findall(teks)
    for tujuan, _ in _POLA_ANCHOR.findall(teks):
        if tujuan.lower().startswith("http"):
            urls.append(tujuan)

    unik, terlihat = [], set()
    for u in urls:
        bersih = u.rstrip(".,;:!?)\"'")
        if bersih not in terlihat:
            terlihat.add(bersih)
            unik.append(bersih)
    return unik


def cari_tautan_menipu(teks: str) -> list[dict]:
    """
    Cari tautan yang TULISANNYA berbeda dengan TUJUANNYA.

    Ini salah satu trik phishing paling efektif: di layar tertulis
    "bri.co.id" tapi begitu diklik justru menuju situs lain. Korban merasa
    sudah memeriksa karena yang terbaca memang alamat yang benar.

    Hanya dilaporkan kalau tulisannya memang berbentuk alamat web - kalau
    tulisannya "Klik di sini", itu wajar dan bukan tanda bahaya.
    """
    temuan = []
    for tujuan, tulisan in _POLA_ANCHOR.findall(teks):
        terlihat = _buang_tag_html(tulisan).strip()

        # Hanya periksa kalau tulisannya menyerupai alamat web
        m = re.search(r"([a-z0-9-]+(?:\.[a-z0-9-]+)+)", terlihat, re.IGNORECASE)
        if not m:
            continue

        domain_terlihat = m.group(1).lower().lstrip("www.")
        domain_tujuan = ""
        mt = re.search(r"https?://([^/\s:?]+)", tujuan, re.IGNORECASE)
        if mt:
            domain_tujuan = mt.group(1).lower().lstrip("www.")

        if not domain_tujuan:
            continue

        # Cocok kalau salah satu bagian dari yang lain (mis. sub.bri.co.id)
        cocok = (
            domain_terlihat == domain_tujuan
            or domain_terlihat.endswith("." + domain_tujuan)
            or domain_tujuan.endswith("." + domain_terlihat)
        )
        if not cocok:
            temuan.append({
                "terlihat": domain_terlihat,
                "tujuan": domain_tujuan,
                "url_penuh": tujuan,
            })

    return temuan


def cek_peniruan_lembaga(nama_tampilan: str, alamat: str, subjek: str) -> dict | None:
    """
    Periksa apakah pengirim MENGAKU sebagai lembaga resmi tapi alamat
    emailnya bukan domain lembaga tersebut.

    Contoh yang tertangkap:
        From: "Bank BRI" <bri.verifikasi2024@gmail.com>

    Bank tidak pernah mengirim email resmi dari Gmail. Pemeriksaan ini
    pasti benar - tidak menebak sama sekali.
    """
    petunjuk = f"{nama_tampilan} {subjek}".lower()
    domain = _domain_dari_email(alamat)
    if not domain:
        return None

    for lembaga, domain_resmi in LEMBAGA_RESMI.items():
        # Nama lembaga harus muncul sebagai kata utuh, bukan potongan.
        # Tanpa syarat ini, "dana" akan nyangkut di kata "pendanaan".
        if not re.search(rf"\b{re.escape(lembaga)}\b", petunjuk):
            continue

        if any(domain == d or domain.endswith("." + d) for d in domain_resmi):
            return None  # memang domain resminya, aman

        return {
            "lembaga": lembaga,
            "domain_dipakai": domain,
            "domain_resmi": domain_resmi[0],
            "dari_email_gratis": domain in EMAIL_GRATIS,
        }

    return None


# ============================================================
# FUNGSI UTAMA
# ============================================================

def extract_email_features(mentah: str) -> dict:
    """
    Ambil semua fitur dari sebuah email.

    Args:
        mentah: email mentah lengkap dengan header, ATAU teks hasil
                salin-tempel dari aplikasi email.

    Returns:
        dict berisi fitur angka + beberapa temuan rinci yang dipakai
        lapisan aturan untuk menyusun penjelasan.
    """
    bagian = parse_email(mentah)
    body = bagian["body"]
    subjek = bagian["subject"]
    teks_periksa = f"{subjek}\n{body}"
    teks_bersih = _buang_tag_html(teks_periksa)

    f = {}

    # ---------- Ukuran ----------
    f["panjang_teks"] = len(teks_bersih)
    f["punya_header"] = 1 if bagian["punya_header"] else 0
    f["is_html"] = 1 if re.search(r"<(a|div|table|body|html)\b", body, re.I) else 0

    # ---------- Pengirim ----------
    domain_pengirim = _domain_dari_email(bagian["from_addr"])
    f["dari_email_gratis"] = 1 if domain_pengirim in EMAIL_GRATIS else 0

    # Alamat balasan berbeda dari pengirim: balasan korban diam-diam
    # dialihkan ke kotak surat penipu.
    domain_balasan = _domain_dari_email(bagian["reply_to"])
    f["reply_to_beda"] = (
        1 if domain_balasan and domain_pengirim and domain_balasan != domain_pengirim
        else 0
    )

    domain_return = _domain_dari_email(bagian["return_path"])
    f["return_path_beda"] = (
        1 if domain_return and domain_pengirim and domain_return != domain_pengirim
        else 0
    )

    # ---------- Peniruan lembaga ----------
    peniruan = cek_peniruan_lembaga(
        bagian["from_name"], bagian["from_addr"], subjek
    )
    f["meniru_lembaga"] = 1 if peniruan else 0

    # ---------- Bahasa yang dipakai ----------
    kata_mendesak = _hitung_kata(teks_bersih, KATA_MENDESAK)
    kata_data = _hitung_kata(teks_bersih, KATA_MINTA_DATA)
    kata_hadiah = _hitung_kata(teks_bersih, KATA_HADIAH)

    f["jumlah_kata_mendesak"] = len(kata_mendesak)
    f["jumlah_kata_minta_data"] = len(kata_data)
    f["jumlah_kata_hadiah"] = len(kata_hadiah)

    # ---------- Tautan ----------
    tautan = ambil_tautan(body)
    menipu = cari_tautan_menipu(body)
    f["jumlah_tautan"] = len(tautan)
    f["jumlah_tautan_menipu"] = len(menipu)

    # ---------- Lampiran ----------
    # Digabung dari dua sumber: struktur MIME (kalau emailnya utuh) DAN
    # nama berkas yang tertulis sebagai teks biasa (kalau emailnya hasil
    # salin-tempel). Lihat penjelasan di _POLA_NAMA_BERKAS.
    daftar_lampiran = list(bagian["attachments"])

    # Alamat web dibuang lebih dulu. Tanpa ini "github.com" terbaca sebagai
    # berkas bernama "github" berekstensi ".com" - dan ".com" memang
    # ekstensi program warisan DOS, sehingga notifikasi GitHub dan
    # Tokopedia ikut divonis berisi lampiran berbahaya. Kesalahan nyata
    # yang muncul saat pengujian.
    teks_tanpa_url = _POLA_URL.sub(" ", teks_periksa)
    teks_tanpa_url = re.sub(r"[\w.-]+@[\w.-]+", " ", teks_tanpa_url)  # buang alamat email

    for kandidat in _POLA_NAMA_BERKAS.findall(teks_tanpa_url):
        kandidat = kandidat.strip()
        rendah = kandidat.lower()
        potong = rendah.rsplit(".", 1)
        ext = potong[-1] if len(potong) > 1 else ""

        ekstensi_ganda = bool(re.search(
            r"\.(pdf|doc|docx|xls|xlsx|jpg|png|txt)\.[a-z0-9]{2,4}$", rendah
        ))

        # Ekstensi ganda selalu diambil - polanya terlalu khas untuk kebetulan.
        # Ekstensi tunggal baru diambil bila ada kata yang menandakan lampiran
        # di dekatnya, karena banyak ekstensi berbahaya yang juga merupakan
        # akhiran domain: .com, .app, .zip, .sh, .cc
        if ekstensi_ganda:
            layak = True
        elif ext in EKSTENSI_BERBAHAYA or ext in EKSTENSI_WASPADA:
            posisi = teks_tanpa_url.lower().find(rendah)
            sekitar = teks_tanpa_url.lower()[max(0, posisi - 120):posisi + 40]
            layak = bool(re.search(
                r"lampir|terlampir|attach|filename|dokumen|berkas|unduh|download",
                sekitar
            ))
        else:
            layak = False

        if layak and kandidat not in daftar_lampiran:
            daftar_lampiran.append(kandidat)

    berbahaya, waspada, ganda = [], [], []
    for nama in daftar_lampiran:
        potong = nama.lower().rsplit(".", 1)
        ext = potong[-1] if len(potong) > 1 else ""

        if ext in EKSTENSI_BERBAHAYA:
            berbahaya.append(nama)
        elif ext in EKSTENSI_WASPADA:
            waspada.append(nama)

        # Nama berekstensi ganda, contoh "invoice.pdf.exe". Windows sering
        # menyembunyikan ekstensi terakhir, jadi korban cuma melihat ".pdf".
        if re.search(r"\.(pdf|doc|docx|xls|xlsx|jpg|png|txt)\.[a-z0-9]{2,4}$",
                     nama.lower()):
            ganda.append(nama)

    f["jumlah_lampiran"] = len(daftar_lampiran)
    f["lampiran_berbahaya"] = len(berbahaya)
    f["lampiran_waspada"] = len(waspada)
    f["lampiran_ekstensi_ganda"] = len(ganda)

    # ---------- Temuan rinci untuk menyusun penjelasan ----------
    f["_rinci"] = {
        "from_addr": bagian["from_addr"],
        "from_name": bagian["from_name"],
        "reply_to": bagian["reply_to"],
        "subject": subjek,
        "peniruan": peniruan,
        "kata_mendesak": kata_mendesak[:5],
        "kata_minta_data": kata_data[:5],
        "kata_hadiah": kata_hadiah[:5],
        "tautan": tautan[:20],
        "tautan_menipu": menipu[:5],
        "lampiran_berbahaya": berbahaya,
        "lampiran_waspada": waspada,
        "lampiran_ganda": ganda,
    }

    return f
