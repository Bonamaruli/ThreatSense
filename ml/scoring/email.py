"""
predict_email.py
================
Mesin penilaian email phishing.

CARA KERJA
----------
Email dinilai dari dua sisi yang saling menguatkan:

  1. ISI EMAIL - aturan terhadap header dan tulisannya: pengirim mengaku
     bank tapi memakai Gmail, alamat balasan dialihkan, tautan yang
     tulisannya beda dengan tujuannya, lampiran .exe menyamar jadi .pdf.

  2. TAUTAN DI DALAMNYA - setiap tautan dinilai memakai ml/predict.py,
     mesin URL yang sudah selesai dibuat. Jadi email yang memuat tautan
     judi atau peniruan merek langsung ikut tertangkap tanpa perlu aturan
     baru. Ini alasan URL Scanner dikerjakan lebih dulu: hasilnya dipakai
     ulang di sini.

Skor akhir diambil dari aturan yang paling berat (bukan dijumlahkan),
sama seperti mesin URL. Alasannya: satu bukti kuat sudah cukup untuk
memvonis, dan menjumlahkan banyak sinyal lemah gampang melahirkan tuduhan
salah pada email biasa yang kebetulan memuat kata "segera".

BATAS YANG PERLU DISADARI
-------------------------
Pemeriksaan ini TIDAK memverifikasi SPF/DKIM/DMARC, karena itu butuh
menghubungi server DNS pengirim dan header lengkap yang jarang dimiliki
pengguna biasa saat menyalin email. Artinya pemalsuan alamat pengirim
yang rapi masih bisa lolos. Ini ditulis terus terang, bukan disembunyikan.
"""

from ml.features.email_features import extract_email_features
from ml.scoring.url import predict_url

# Batas nilai, disamakan dengan mesin URL supaya artinya konsisten
AMBANG_BERBAHAYA = 0.70
AMBANG_MENCURIGAKAN = 0.40

# Tautan berbahaya di dalam email tidak diteruskan 100% ke skor email.
# Alasannya: sebuah email bisa saja MEMBAHAS tautan berbahaya tanpa
# bermaksud jahat - misalnya laporan keamanan, atau email dari dosen yang
# mencontohkan situs phishing. Nilainya tetap tinggi, tapi tidak otomatis
# memvonis kalau tidak ada tanda lain.
PENERUSAN_SKOR_TAUTAN = 0.85

# Jumlah tautan yang diperiksa. Dibatasi supaya email berisi ratusan tautan
# tidak membuat satu permintaan berjalan lama sekali.
MAKS_TAUTAN_DIPERIKSA = 15


def evaluasi_aturan(f: dict) -> list[dict]:
    """Jalankan semua aturan terhadap isi dan header email."""
    menyala = []
    rinci = f.get("_rinci", {})

    def tambah(bobot, judul, alasan):
        menyala.append({"bobot": bobot, "aturan": judul, "alasan": alasan})

    # ---------- Peniruan lembaga ----------
    peniruan = rinci.get("peniruan")
    if peniruan:
        if peniruan["dari_email_gratis"]:
            tambah(0.95, "Mengaku lembaga resmi dari email gratis",
                   f"Pengirim mengaku sebagai '{peniruan['lembaga'].upper()}' "
                   f"tapi memakai alamat {peniruan['domain_dipakai']} "
                   f"(layanan email gratis). Lembaga resmi selalu memakai "
                   f"domain sendiri, yaitu {peniruan['domain_resmi']}.")
        else:
            tambah(0.90, "Alamat pengirim bukan domain resmi",
                   f"Pengirim mengaku sebagai '{peniruan['lembaga'].upper()}' "
                   f"tapi alamatnya {peniruan['domain_dipakai']}, bukan "
                   f"{peniruan['domain_resmi']}.")

    # ---------- Tautan menipu ----------
    menipu = rinci.get("tautan_menipu") or []
    if menipu:
        c = menipu[0]
        tambah(0.90, "Tautan menipu",
               f"Ada tautan yang di layar tertulis '{c['terlihat']}' tapi "
               f"sebenarnya mengarah ke '{c['tujuan']}'. Korban merasa sudah "
               f"memeriksa karena yang terbaca alamat yang benar.")

    # ---------- Lampiran ----------
    if f.get("lampiran_ekstensi_ganda"):
        nama = rinci.get("lampiran_ganda", ["?"])[0]
        tambah(0.95, "Lampiran berekstensi ganda",
               f"Lampiran '{nama}' memakai dua ekstensi. Windows sering "
               f"menyembunyikan ekstensi terakhir, sehingga yang terlihat "
               f"hanya bagian depannya yang tampak aman.")

    if f.get("lampiran_berbahaya"):
        nama = rinci.get("lampiran_berbahaya", ["?"])[0]
        tambah(0.90, "Lampiran bisa menjalankan program",
               f"Lampiran '{nama}' berjenis berkas yang bisa langsung "
               f"menjalankan perintah di komputermu begitu dibuka.")

    if f.get("lampiran_waspada"):
        nama = rinci.get("lampiran_waspada", ["?"])[0]
        tambah(0.55, "Lampiran bisa memuat makro",
               f"Lampiran '{nama}' bisa menyimpan makro atau berkas "
               f"tersembunyi di dalamnya. Jangan aktifkan konten bila diminta.")

    # ---------- Alamat balasan dialihkan ----------
    if f.get("reply_to_beda"):
        tambah(0.65, "Balasan dialihkan ke alamat lain",
               f"Balasanmu tidak akan menuju pengirim, melainkan ke "
               f"{rinci.get('reply_to', '(lain)')}. Trik agar percakapan "
               f"lanjutan masuk ke kotak surat penipu.")

    if f.get("return_path_beda") and not f.get("reply_to_beda"):
        tambah(0.45, "Jalur pengiriman tidak cocok",
               "Jalur asal email berbeda dengan alamat pengirim yang "
               "ditampilkan. Bisa tanda pemalsuan, bisa juga karena email "
               "dikirim lewat layanan pihak ketiga.")

    # ---------- Meminta data rahasia ----------
    kata_data = rinci.get("kata_minta_data") or []
    if kata_data:
        if f.get("jumlah_tautan"):
            tambah(0.85, "Meminta data rahasia lewat tautan",
                   f"Email menyebut {', '.join(kata_data[:3])} sekaligus "
                   f"memuat tautan. Bank dan lembaga resmi TIDAK PERNAH "
                   f"meminta data ini lewat email.")
        else:
            tambah(0.60, "Meminta data rahasia",
                   f"Email menyebut {', '.join(kata_data[:3])}. Lembaga resmi "
                   f"tidak pernah meminta data ini lewat email.")

    # ---------- Bahasa mendesak ----------
    mendesak = rinci.get("kata_mendesak") or []
    if len(mendesak) >= 2:
        tambah(0.55, "Menekan agar buru-buru",
               f"Email memakai kata seperti {', '.join(mendesak[:3])}. "
               f"Menakut-nakuti agar korban bertindak sebelum sempat berpikir "
               f"adalah pola paling umum dalam penipuan.")
    elif mendesak:
        tambah(0.30, "Ada kesan mendesak",
               f"Email memakai kata '{mendesak[0]}'. Wajar untuk sebagian "
               f"pesan, jadi baru berarti bila digabung tanda lain.")

    # ---------- Iming-iming hadiah ----------
    hadiah = rinci.get("kata_hadiah") or []
    if len(hadiah) >= 2:
        tambah(0.60, "Menjanjikan hadiah",
               f"Email menjanjikan {', '.join(hadiah[:3])}. Umpan klasik "
               f"untuk memancing korban mengeklik atau menyerahkan data.")

    # ---------- Pengirim email gratis tanpa identitas jelas ----------
    if f.get("dari_email_gratis") and not peniruan and f.get("jumlah_tautan"):
        tambah(0.35, "Dikirim dari email gratis",
               "Dikirim dari layanan email gratis dan memuat tautan. Bukan "
               "tanda bahaya kalau memang dari kenalan, tapi patut dicek bila "
               "mengaku dari sebuah lembaga.")

    return menyala


def predict_email(mentah: str) -> dict:
    """
    Nilai sebuah email.

    Returns dict dengan bentuk yang sama seperti predict_url(), supaya
    backend dan frontend bisa memperlakukan keduanya secara seragam.
    """
    f = extract_email_features(mentah)
    rinci = f.get("_rinci", {})

    # --- Sisi 1: aturan terhadap isi email ---
    aturan = evaluasi_aturan(f)
    skor_aturan = max((a["bobot"] for a in aturan), default=0.0)

    # --- Sisi 2: nilai setiap tautan memakai mesin URL ---
    tautan = (rinci.get("tautan") or [])[:MAKS_TAUTAN_DIPERIKSA]
    hasil_tautan, skor_tautan_tertinggi, tautan_terburuk = [], 0.0, None

    for u in tautan:
        try:
            h = predict_url(u)
        except Exception:
            continue

        hasil_tautan.append({
            "url": u,
            "risk_score": h["risk_score"],
            "threat_label": h["threat_label"],
            "rules_fired": h["rules_fired"],
        })

        if h["risk_score"] > skor_tautan_tertinggi:
            skor_tautan_tertinggi = h["risk_score"]
            tautan_terburuk = h
            tautan_terburuk["_url"] = u

    skor_dari_tautan = skor_tautan_tertinggi * PENERUSAN_SKOR_TAUTAN
    skor = round(min(max(max(skor_aturan, skor_dari_tautan), 0.0), 1.0), 4)

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

    if tautan_terburuk and skor_tautan_tertinggi >= AMBANG_MENCURIGAKAN:
        sebab = tautan_terburuk["rules_fired"]
        penjelasan.append({
            "judul": "Memuat tautan berbahaya",
            "alasan": (
                f"Salah satu tautan di email ini dinilai "
                f"{tautan_terburuk['threat_label']} "
                f"({tautan_terburuk['risk_score']*100:.0f}%)"
                + (f" karena {sebab[0].lower()}." if sebab else ".")
                + f" Alamatnya: {tautan_terburuk['_url'][:70]}"
            ),
            "bobot": round(skor_dari_tautan, 3),
        })

    if not penjelasan:
        penjelasan.append({
            "judul": "Tidak ditemukan tanda bahaya",
            "alasan": ("Tidak ada aturan yang dilanggar dan tautannya wajar. "
                       "Catatan: pemeriksaan ini belum memverifikasi keaslian "
                       "pengirim lewat SPF/DKIM, jadi pemalsuan yang rapi "
                       "masih mungkin lolos."),
            "bobot": 0.0,
        })

    if not f.get("punya_header"):
        penjelasan.append({
            "judul": "Header email tidak tersedia",
            "alasan": ("Yang ditempel hanya isi email, tanpa header. "
                       "Pemeriksaan pengirim dan alamat balasan dilewati. "
                       "Untuk hasil lebih lengkap, salin email beserta "
                       "headernya lewat menu 'Show original' di Gmail."),
            "bobot": 0.0,
        })

    # Buang bagian rinci sebelum disimpan ke database - isinya memuat
    # cuplikan email yang tidak perlu ikut tersimpan.
    fitur_bersih = {k: v for k, v in f.items() if not k.startswith("_")}

    return {
        "risk_score": skor,
        "threat_label": label,
        "features": fitur_bersih,
        "explanations": penjelasan,
        "rules_fired": [a["aturan"] for a in aturan],
        "link_results": hasil_tautan,
    }


if __name__ == "__main__":
    contoh = """From: "Bank BRI" <bri.verifikasi2024@gmail.com>
Reply-To: penampung.data@mail.ru
Subject: SEGERA - Rekening Anda Akan Diblokir Dalam 24 Jam

Nasabah yang terhormat,

Kami mendeteksi aktivitas mencurigakan. Rekening Anda akan diblokir
dalam 24 jam. Segera verifikasi kata sandi dan PIN Anda melalui tautan
berikut:

<a href="http://bri-verifikasi-nasabah.tk/login">https://bri.co.id/verifikasi</a>

Jangan abaikan pesan ini.
"""
    h = predict_email(contoh)
    print(f"{h['threat_label']}  {h['risk_score']*100:.0f}%\n")
    for p in h["explanations"]:
        print(f"  [{p['bobot']:.2f}] {p['judul']}")
        print(f"         {p['alasan'][:100]}")
