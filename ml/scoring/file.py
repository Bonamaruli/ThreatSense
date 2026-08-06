"""
predict_file.py
===============
Menilai berkas berdasarkan hasil analisis statis.

KENAPA ATURAN, BUKAN MODEL TERLATIH
-----------------------------------
Untuk melatih model deteksi malware dibutuhkan ribuan contoh berkas jahat
sungguhan. Menyimpan koleksi malware di laptop pribadi adalah risiko nyata,
dan tidak sepadan untuk keperluan tugas akhir.

Kabar baiknya, ciri-ciri paling menentukan di sini memang bisa dinyatakan
sebagai aturan yang tegas dan bisa dibaca manusia:

    berkas bernama "faktur.pdf" yang isinya program Windows

Itu bukan pola samar yang perlu dipelajari model - itu kejanggalan yang
bisa langsung dijelaskan, dan justru lebih meyakinkan karena alasannya
terbaca. Kalau nanti tersedia dataset malware yang aman dipakai, lapisan
model bisa ditambahkan di atas aturan ini tanpa membongkar apa pun.

Batasan ini ditulis terbuka di laporan, bukan disembunyikan.
"""

from __future__ import annotations

from typing import Any

from ml.features.file_features import extract_file_features

AMBANG_BERBAHAYA = 0.70
AMBANG_MENCURIGAKAN = 0.40


def _aturan(f: dict[str, Any]) -> list[dict]:
    """Terjemahkan temuan jadi daftar alasan berbobot."""
    temuan: list[dict] = []

    def tambah(bobot, judul, alasan):
        temuan.append({"bobot": bobot, "aturan": judul, "alasan": alasan})

    jenis = f.get("jenis_asli")
    ekst = f.get("ekstensi")

    # ---------- Isi berkas tidak sesuai namanya ----------
    # Ini temuan terkuat yang bisa dihasilkan analisis statis.
    if f.get("ekstensi_cocok_isi") is False:
        if jenis and jenis.startswith("executable"):
            tambah(0.95, "Isinya program, bukan seperti namanya",
                   f"Berkas ini bernama '.{ekst}' tetapi isi sebenarnya adalah "
                   f"{f.get('jenis_keterangan')}. Penyamaran seperti ini hampir "
                   f"tidak punya alasan yang sah - berkas dokumen tidak mungkin "
                   f"berisi program.")
        else:
            tambah(0.55, "Isi tidak cocok dengan ekstensinya",
                   f"Berkas bernama '.{ekst}' tetapi isinya "
                   f"{f.get('jenis_keterangan')}. Perlu diperiksa lebih teliti.")

    # ---------- Ekstensi ganda ----------
    if f.get("ekstensi_ganda"):
        tambah(0.90, "Ekstensi ganda menyamarkan jenis berkas",
               f"Nama berkasnya berakhiran '{f.get('ekstensi_ganda_pola')}'. "
               f"Mata pembaca berhenti di bagian yang tampak aman dan "
               f"melewatkan bagian akhirnya - berkas ini sebenarnya bisa "
               f"langsung dijalankan.")

    # ---------- Berkas yang bisa langsung dijalankan ----------
    elif f.get("bisa_langsung_jalan"):
        tambah(0.55, "Berkas bisa langsung dijalankan",
               f"Berkas '.{ekst}' dijalankan begitu dibuka. Pastikan kamu "
               f"benar-benar mengharapkan berkas ini dari pengirimnya.")

    # ---------- Makro di dokumen Office ----------
    if f.get("ada_makro"):
        tambah(0.80, "Dokumen membawa makro",
               "Dokumen ini memuat makro - program yang ikut di dalamnya. "
               "Surat atau faktur biasa tidak perlu membawa program, dan "
               "makro di lampiran yang tidak diminta adalah cara penyebaran "
               "malware yang masih sangat umum.")

    # ---------- Program di dalam arsip ----------
    if (f.get("berkas_bisa_jalan_di_arsip") or 0) > 0:
        tambah(0.75, "Ada program di dalam arsip",
               f"Arsip ini berisi {f['berkas_bisa_jalan_di_arsip']} berkas yang "
               f"bisa langsung dijalankan, contohnya "
               f"'{f.get('contoh_berkas_bahaya')}'. Mengemas program di dalam "
               f"arsip dipakai untuk melewati pemindaian lampiran email.")

    if (f.get("arsip_bertingkat") or 0) > 0:
        tambah(0.50, "Arsip di dalam arsip",
               "Arsip ini memuat arsip lain di dalamnya. Penumpukan seperti "
               "ini sering dipakai supaya isinya tidak terbaca pemindai.")

    # ---------- PDF ----------
    if f.get("pdf_javascript") and f.get("pdf_auto_jalan"):
        tambah(0.85, "PDF menjalankan program otomatis saat dibuka",
               "PDF ini memuat JavaScript DAN perintah yang berjalan otomatis "
               "begitu berkas dibuka. Dokumen untuk dibaca tidak perlu "
               "keduanya.")
    elif f.get("pdf_javascript"):
        tambah(0.55, "PDF memuat JavaScript",
               "PDF ini memuat program JavaScript. Sebagian formulir resmi "
               "memang memakainya, jadi ini baru berarti bila ditemani tanda "
               "lain.")

    if f.get("pdf_luncurkan"):
        tambah(0.80, "PDF bisa menjalankan berkas lain",
               "PDF ini memuat perintah untuk menjalankan berkas lain di "
               "komputermu. Dokumen bacaan tidak pernah perlu itu.")

    if f.get("pdf_sematan"):
        tambah(0.50, "PDF menyembunyikan berkas di dalamnya",
               "Ada berkas lain yang disematkan di dalam PDF ini.")

    # ---------- Entropi tinggi ----------
    # Hanya berarti untuk jenis yang seharusnya TIDAK termampatkan. Gambar
    # dan arsip memang wajar beracak - menuduhnya akan salah terus.
    if f.get("entropi_tinggi") and jenis in ("executable-windows",
                                             "executable-linux", "ole",
                                             "tidak-dikenal"):
        tambah(0.45, "Isi berkas teracak",
               f"Isi berkas ini sangat acak (entropi {f.get('entropi')} dari "
               f"maksimum 8,0), tanda bahwa berkasnya dipak atau dienkripsi "
               f"agar sulit diperiksa.")

    if f.get("arsip_rusak"):
        tambah(0.40, "Arsip tidak bisa dibuka",
               "Berkas ini mengaku arsip tapi isinya rusak atau dilindungi "
               "sandi, sehingga tidak bisa diperiksa. Arsip berkata sandi "
               "sering dipakai untuk menghindari pemindaian.")

    return temuan


def predict_file(nama_berkas: str, data: bytes) -> dict[str, Any]:
    """
    Nilai sebuah berkas.

    Berkasnya TIDAK PERNAH dijalankan - hanya dibaca sebagai data.
    """
    fitur = extract_file_features(nama_berkas, data)
    aturan = _aturan(fitur)

    skor = max((a["bobot"] for a in aturan), default=0.0)
    skor = round(min(max(skor, 0.0), 1.0), 4)

    if skor >= AMBANG_BERBAHAYA:
        label = "Malicious"
    elif skor >= AMBANG_MENCURIGAKAN:
        label = "Suspicious"
    else:
        label = "Safe"

    penjelasan = [
        {"judul": a["aturan"], "alasan": a["alasan"], "bobot": a["bobot"]}
        for a in sorted(aturan, key=lambda a: -a["bobot"])
    ]

    if fitur.get("berkas_kosong"):
        penjelasan.append({
            "judul": "Berkas kosong",
            "alasan": "Tidak ada isi yang bisa diperiksa.",
            "bobot": 0.0,
        })
    elif not aturan:
        penjelasan.append({
            "judul": "Tidak ditemukan tanda bahaya",
            "alasan": (
                f"Isi berkas cocok dengan namanya ({fitur.get('jenis_keterangan')}), "
                f"tidak membawa makro atau program di dalamnya. Catatan: "
                f"pemeriksaan ini membaca struktur berkas, bukan mencocokkannya "
                f"dengan daftar malware yang sudah dikenal."
            ),
            "bobot": 0.0,
        })

    # Bukti netral untuk ditampilkan apa adanya
    ringkasan = [
        {"label": "Nama berkas", "nilai": fitur["nama_berkas"]},
        {"label": "Ukuran", "nilai": f"{fitur['ukuran_byte']:,} byte"},
        {"label": "Jenis sebenarnya", "nilai": fitur.get("jenis_keterangan") or "-"},
        {"label": "Ekstensi", "nilai": f".{fitur.get('ekstensi')}" if fitur.get("ekstensi") else "-"},
        {"label": "Entropi", "nilai": f"{fitur.get('entropi')} / 8.0"},
        {"label": "SHA-256", "nilai": fitur["sha256"]},
    ]
    if fitur.get("jumlah_berkas_arsip"):
        ringkasan.append({"label": "Isi arsip",
                          "nilai": f"{fitur['jumlah_berkas_arsip']} berkas"})
    if fitur.get("ada_makro"):
        ringkasan.append({"label": "Makro", "nilai": "Ada"})

    return {
        "risk_score": skor,
        "threat_label": label,
        "features": fitur,
        "explanations": penjelasan,
        "evidence_summary": ringkasan,
        "rules_fired": [a["aturan"] for a in aturan],
    }
