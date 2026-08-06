"""
deep_vector.py
==============
Mengubah BUKTI hasil analisis mendalam menjadi deretan angka untuk model.

KENAPA PERLU BERKAS TERPISAH
----------------------------
analisis_mendalam() menghasilkan campuran teks, tanggal, dan True/False -
bentuk yang enak dibaca manusia tapi tidak bisa dicerna model. Di sini
semuanya diterjemahkan jadi angka, dengan aturan yang konsisten.

ATURAN PENTING: BEDAKAN "NOL" DARI "TIDAK DIPERIKSA"
----------------------------------------------------
Kalau WHOIS gagal, umur domain tidak diketahui. Menuliskannya sebagai 0
akan berbohong pada model - 0 berarti "domain didaftarkan hari ini", yang
justru sinyal bahaya. Karena itu nilai yang tidak diketahui ditulis -1,
dan disertai penanda terpisah (ada_data_whois) supaya model bisa belajar
membedakan "muda" dari "tidak terbaca".

Kelalaian semacam ini mudah terjadi dan sulit ketahuan: modelnya tetap
terlatih, akurasinya tetap keluar, hanya saja belajar dari data yang salah.
"""

from __future__ import annotations

from typing import Any

# Negara yang paling sering muncul sebagai lokasi server. Diubah jadi kolom
# 0/1 masing-masing, bukan satu kolom berisi nama negara - model pohon tidak
# bisa membaca teks, dan memberi nomor urut pada negara (1=AS, 2=Rusia, ...)
# akan menyiratkan urutan yang tidak ada artinya.
NEGARA_DIPANTAU = ["US", "ID", "SG", "RU", "CN", "NL", "DE", "FR", "GB", "IN"]


def _angka(nilai, bawaan: float = -1.0) -> float:
    """Ubah ke angka; nilai kosong jadi -1 (artinya 'tidak diketahui')."""
    if nilai is None:
        return bawaan
    try:
        return float(nilai)
    except (TypeError, ValueError):
        return bawaan


def _biner(nilai) -> int:
    """True/False jadi 1/0. None juga jadi 0, tapi selalu ditemani penanda
    'apakah pemeriksaannya berhasil' di kolom lain."""
    return 1 if nilai is True else 0


def vektor_dari_bukti(bukti: dict[str, Any]) -> dict[str, float]:
    """
    Ubah hasil analisis_mendalam() jadi fitur angka.

    Nama kolomnya sengaja diawali 'd_' (dalam) supaya tidak bentrok dengan
    fitur nama domain, dan langsung kelihatan asalnya saat membaca daftar
    fitur terpenting nanti.
    """
    f: dict[str, float] = {}

    # ---------- Pendaftaran domain ----------
    umur = bukti.get("umur_domain_hari")
    f["d_ada_data_whois"] = 1 if umur is not None else 0
    f["d_umur_hari"] = _angka(umur)
    # Umur dipecah jadi beberapa ambang. Pohon keputusan sebenarnya bisa
    # mencari ambangnya sendiri, tapi ambang yang bermakna secara keamanan
    # membuat model lebih cepat menemukan pola yang benar dari data sedikit.
    f["d_umur_dibawah_7hari"] = 1 if (umur is not None and umur <= 7) else 0
    f["d_umur_dibawah_30hari"] = 1 if (umur is not None and umur <= 30) else 0
    f["d_umur_dibawah_180hari"] = 1 if (umur is not None and umur <= 180) else 0
    f["d_umur_diatas_3tahun"] = 1 if (umur is not None and umur >= 1095) else 0

    # ---------- Lokasi server ----------
    kode = (bukti.get("kode_negara_hosting") or "").upper()
    f["d_negara_diketahui"] = 1 if kode else 0
    for n in NEGARA_DIPANTAU:
        f[f"d_negara_{n}"] = 1 if kode == n else 0
    f["d_negara_lain"] = 1 if (kode and kode not in NEGARA_DIPANTAU) else 0
    f["d_punya_ip"] = 1 if bukti.get("ip") else 0

    # ---------- Sertifikat ----------
    ssl_ada = bukti.get("ssl_ada")
    f["d_ssl_diperiksa"] = 1 if ssl_ada is not None else 0
    f["d_ssl_ada"] = _biner(ssl_ada)
    f["d_ssl_cocok"] = _biner(bukti.get("ssl_cocok_domain"))
    f["d_ssl_umur_hari"] = _angka(bukti.get("ssl_umur_hari"))
    f["d_ssl_masih_baru"] = 1 if _angka(bukti.get("ssl_umur_hari"), 9e9) <= 30 else 0

    # ---------- Perilaku saat dibuka ----------
    status = bukti.get("status_http")
    f["d_bisa_dibuka"] = 1 if status is not None else 0
    f["d_status_200"] = 1 if status == 200 else 0
    f["d_status_4xx"] = 1 if (status and 400 <= status < 500) else 0
    f["d_jumlah_pengalihan"] = _angka(bukti.get("jumlah_pengalihan"), 0)
    f["d_pindah_domain"] = _biner(bukti.get("pindah_domain"))

    # ---------- Isi halaman ----------
    terbaca = bukti.get("halaman_terbaca")
    f["d_halaman_terbaca"] = _biner(terbaca)
    f["d_ada_kolom_sandi"] = _biner(bukti.get("ada_kolom_sandi"))
    f["d_jumlah_kolom_sandi"] = _angka(bukti.get("jumlah_kolom_sandi"), 0)
    f["d_jumlah_form"] = _angka(bukti.get("jumlah_form"), 0)
    f["d_form_ke_domain_lain"] = _biner(bukti.get("form_kirim_ke_domain_lain"))
    f["d_kata_kredensial"] = _angka(bukti.get("kata_kredensial_di_halaman"), 0)
    f["d_kata_judi"] = _angka(bukti.get("kata_judi_di_halaman"), 0)
    f["d_kata_judi_kuat"] = _angka(bukti.get("kata_judi_kuat_di_halaman"), 0)
    f["d_sebut_merek_lain"] = 1 if bukti.get("merek_disebut_di_halaman") else 0
    f["d_iframe_tersembunyi"] = _angka(bukti.get("iframe_tersembunyi"), 0)
    f["d_js_teracak"] = _biner(bukti.get("js_teracak"))
    f["d_ukuran_halaman_kb"] = round(_angka(bukti.get("ukuran_halaman"), 0) / 1024, 2)
    f["d_panjang_judul"] = len(bukti.get("judul_halaman") or "")
    f["d_punya_judul"] = 1 if bukti.get("judul_halaman") else 0

    # ---------- Gabungan yang bermakna ----------
    # Kombinasi inilah yang tidak bisa ditangkap fitur tunggal, dan justru
    # jadi alasan utama memakai model: "minta sandi" saja wajar, "domain
    # muda" saja wajar, tapi keduanya bersamaan sangat tidak wajar.
    muda = f["d_umur_dibawah_30hari"]
    sandi = f["d_ada_kolom_sandi"]
    f["d_sandi_dan_domain_muda"] = 1 if (sandi and muda) else 0
    f["d_sandi_dan_sebut_merek"] = 1 if (sandi and f["d_sebut_merek_lain"]) else 0
    f["d_sandi_tanpa_ssl"] = 1 if (sandi and not f["d_ssl_ada"]) else 0
    f["d_sandi_dan_form_asing"] = 1 if (sandi and f["d_form_ke_domain_lain"]) else 0

    return f


# Urutan kolom dipatok dari contoh kosong, supaya susunannya tidak pernah
# bergeser diam-diam saat fungsi di atas diubah. Urutan yang bergeser membuat
# prediksi model kacau tanpa memunculkan error apa pun.
DEEP_FEATURE_NAMES = list(vektor_dari_bukti({}).keys())
