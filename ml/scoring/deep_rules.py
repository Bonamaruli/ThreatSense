"""
deep_rules.py
=============
Menerjemahkan BUKTI hasil analisis mendalam menjadi penilaian dan alasan.

BEDANYA DENGAN ATURAN DI predict.py
-----------------------------------
Aturan di predict.py hanya bisa menebak dari nama domain. Aturan di sini
memakai bukti yang benar-benar diambil dari alamatnya: umur pendaftaran,
negara server, sertifikat, ke mana ia mengalihkan, dan apa isi halamannya.

Itu sebabnya kesimpulan di sini bisa membedakan dua hal yang dari namanya
tampak sama persis:

    toko baru resmi   : umur 5 hari, isi halaman katalog produk  -> aman
    phishing baru     : umur 5 hari, ada kolom sandi + menyebut
                        nama bank padahal bukan domain bank itu  -> bahaya

Umur muda SENDIRIAN tidak berarti apa-apa - setiap situs pernah baru.
Yang menentukan adalah GABUNGANNYA dengan bukti lain. Prinsip itu yang
dipegang di seluruh berkas ini.
"""

from __future__ import annotations

from typing import Any

# Umur domain (hari) yang dianggap sangat muda.
# Situs penipuan biasanya berumur pendek karena cepat dilaporkan dan
# ditutup, lalu penipunya mendaftar domain baru lagi.
UMUR_SANGAT_MUDA = 30
UMUR_MUDA = 90

# Umur (hari) yang membuat sebuah domain dianggap MAPAN.
#
# Angka ini dipakai meredam aturan berbasis isi halaman, dan alasannya
# ditemukan dari dua salah vonis nyata saat pengujian:
#
#   eaa.org (berumur 31 tahun)  -> divonis Berbahaya 95%, karena halamannya
#       punya kolom sandi dan menyebut "google" (tombol "Sign in with
#       Google"). Padahal itu pola login yang sangat lazim.
#
#   accounts.google.com         -> divonis Berbahaya 70%, karena kode
#       halamannya termampatkan berat sehingga terbaca sebagai "disamarkan".
#       Semua situs besar begitu.
#
# Pola yang sama muncul di keduanya: tanda-tanda itu WAJAR pada situs yang
# sudah lama berdiri, dan baru mencurigakan pada domain yang masih baru.
# Penipu jarang punya domain berumur bertahun-tahun - domainnya cepat
# dilaporkan dan ditutup, lalu mereka mendaftar yang baru lagi.
UMUR_MAPAN = 730  # 2 tahun


def _peredam_umur(umur: int | None) -> float:
    """
    Faktor pengali untuk aturan berbasis isi halaman, berdasarkan umur domain.

    Domain mapan meredam kecurigaan; domain muda atau yang umurnya tidak
    terbaca tidak diredam sama sekali.
    """
    if umur is None:
        return 1.0            # tidak diketahui -> jangan diberi keringanan
    if umur >= UMUR_MAPAN * 3:   # 6 tahun ke atas
        return 0.25
    if umur >= UMUR_MAPAN:       # 2 tahun ke atas
        return 0.5
    return 1.0


def evaluasi_bukti(bukti: dict[str, Any]) -> list[dict]:
    """
    Ubah bukti jadi daftar temuan berbobot.

    Tiap temuan berisi bobot risiko (0-1), judul singkat, dan kalimat
    penjelasan yang menyebut bukti konkretnya - bukan sekadar "mencurigakan".
    """
    temuan: list[dict] = []

    umur = bukti.get("umur_domain_hari")
    peredam = _peredam_umur(umur)

    def tambah(bobot: float, judul: str, alasan: str, ikut_diredam: bool = False):
        """
        ikut_diredam=True untuk aturan yang membaca ISI halaman.

        Aturan seperti "ada kolom sandi" atau "kode disamarkan" menandakan
        hal yang sama sekali wajar di situs mapan, tapi mencurigakan di
        domain yang baru. Aturan yang membaca perilaku teknis (form mengirim
        ke domain lain, sertifikat tidak sah) TIDAK diredam - itu tetap
        mencurigakan berapa pun umur domainnya.
        """
        b = bobot * peredam if ikut_diredam else bobot
        if b < 0.15:
            return  # terlalu lemah untuk ditampilkan, hanya jadi kebisingan
        temuan.append({"bobot": round(b, 3), "aturan": judul, "alasan": alasan})

    ada_sandi = bukti.get("ada_kolom_sandi")
    merek = bukti.get("merek_disebut_di_halaman")
    kata_kredensial = bukti.get("kata_kredensial_di_halaman") or 0
    judi = bukti.get("kata_judi_di_halaman") or 0
    judi_kuat = bukti.get("kata_judi_kuat_di_halaman") or 0

    # ---------- Judi online terbukti dari ISI halaman ----------
    # Ini berbeda jauh dari menebak lewat nama domain: kata-katanya benar
    # benar ada di halaman yang dilihat pengunjung.
    if judi_kuat >= 3 or judi >= 8:
        tambah(0.95, "Judi online (terbukti dari isi halaman)",
               f"Halaman ini memuat {judi} kata khas judi ({judi_kuat} di "
               f"antaranya sangat menentukan seperti slot, gacor, atau togel). "
               f"Bukti diambil dari teks yang benar-benar tampil di halaman, "
               f"bukan dari tebakan nama domain.")
    elif judi_kuat >= 1 or judi >= 4:
        tambah(0.80, "Indikasi judi online di halaman",
               f"Ditemukan {judi} kata yang lazim dipakai situs judi di dalam "
               f"isi halaman ini.")

    # ---------- Meminta kredensial sambil menyamar jadi merek lain ----------
    if ada_sandi and merek:
        # Diredam untuk domain mapan: menyebut merek lain di halaman login
        # itu lazim ("Masuk dengan Google"), dan tidak berarti apa-apa pada
        # situs yang sudah berdiri belasan tahun.
        tambah(0.95, "Meminta sandi sambil menyebut merek lain",
               f"Halaman ini punya kolom pengisian sandi DAN menyebut "
               f"'{merek}', padahal alamatnya bukan domain resmi merek "
               f"tersebut. Ini pola paling khas pencurian akun.",
               ikut_diredam=True)
    elif ada_sandi and umur is not None and umur <= UMUR_SANGAT_MUDA:
        tambah(0.90, "Minta sandi padahal domainnya baru",
               f"Halaman meminta sandi, sementara domainnya baru berumur "
               f"{umur} hari. Situs resmi yang meminta sandi hampir selalu "
               f"sudah berdiri lama.")

    # ---------- Isian dikirim ke domain lain ----------
    if bukti.get("form_kirim_ke_domain_lain"):
        tujuan = bukti.get("tujuan_form_asing") or "domain lain"
        bobot = 0.90 if ada_sandi else 0.70
        tambah(bobot, "Data isian dikirim ke pihak lain",
               f"Formulir di halaman ini mengirim isian pengguna ke "
               f"'{tujuan}', bukan ke pemilik alamat yang sedang dibuka. "
               f"Artinya apa pun yang diketik bisa jatuh ke pihak ketiga.")

    # ---------- Umur domain ----------
    if umur is not None:
        if umur <= 7 and not ada_sandi:
            tambah(0.50, "Domain sangat baru",
                   f"Domain ini baru didaftarkan {umur} hari lalu. Belum tentu "
                   f"jahat - setiap situs pernah baru - tapi belum ada rekam "
                   f"jejak yang bisa dipercaya.")
        elif umur <= UMUR_SANGAT_MUDA and not ada_sandi:
            tambah(0.40, "Domain masih muda",
                   f"Umur domain {umur} hari. Perlu kehati-hatian tambahan "
                   f"karena rekam jejaknya masih pendek.")

    # ---------- Pengalihan ke domain lain ----------
    if bukti.get("pindah_domain"):
        akhir = bukti.get("url_akhir") or ""
        tambah(0.55, "Diam-diam berpindah ke situs lain",
               f"Saat dibuka, alamat ini tidak berhenti di tempat yang kamu "
               f"ketik, melainkan berpindah ke {akhir[:60]}. Penyamaran "
               f"tujuan seperti ini sering dipakai untuk menyembunyikan "
               f"halaman aslinya.")

    # ---------- Sertifikat bermasalah ----------
    if bukti.get("ssl_ada") is True and bukti.get("ssl_cocok_domain") is False:
        tambah(0.60, "Sertifikat keamanan tidak sah",
               "Situs ini memakai sertifikat pengaman yang tidak cocok "
               "dengan alamatnya. Peramban biasanya menolak halaman seperti "
               "ini dengan peringatan besar.")
    elif bukti.get("ssl_ada") is False and ada_sandi:
        tambah(0.75, "Minta sandi tanpa pengaman",
               "Halaman ini meminta sandi tapi sambungannya tidak "
               "terenkripsi. Apa pun yang diketik bisa dibaca di jalan.")

    # ---------- Kode yang sengaja disamarkan ----------
    if bukti.get("js_teracak"):
        # Lebih berarti kalau halamannya juga meminta sandi. Banyak situs sah
        # memampatkan kodenya, jadi ini sendirian bukan bukti kuat.
        # Semua situs besar memampatkan kodenya, jadi sinyal ini nyaris tidak
        # berarti pada domain mapan - terbukti saat accounts.google.com
        # sempat divonis berbahaya karenanya.
        if ada_sandi:
            tambah(0.70, "Kode disamarkan di halaman yang minta sandi",
                   "Halaman meminta sandi dan kodenya ditulis teracak agar "
                   "sulit dibaca. Penyamaran seperti ini biasanya untuk "
                   "menyembunyikan ke mana data dikirim.",
                   ikut_diredam=True)
        else:
            tambah(0.35, "Kode halaman disamarkan",
                   "Halaman memuat program yang ditulis dengan cara diacak. "
                   "Sebagian situs sah juga begitu untuk memperkecil ukuran, "
                   "jadi ini baru berarti bila ditemani tanda lain.",
                   ikut_diredam=True)

    # ---------- Bingkai tersembunyi ----------
    #
    # Bobotnya sengaja rendah kalau berdiri sendiri. Alasannya ditemukan saat
    # pengujian: halaman Tokopedia punya 1 bingkai tersembunyi dan sempat
    # divonis "Mencurigakan 60%". Padahal situs besar rutin memakainya untuk
    # analitik, iklan, dan piksel pelacak - sama sekali bukan pertanda jahat.
    #
    # Yang benar-benar mencurigakan adalah JUMLAHNYA yang banyak, atau
    # kemunculannya bersama permintaan sandi.
    n_iframe = bukti.get("iframe_tersembunyi") or 0
    if n_iframe > 0:
        if ada_sandi:
            tambah(0.70, "Bingkai tersembunyi di halaman yang minta sandi",
                   f"Halaman ini meminta sandi DAN menyembunyikan "
                   f"{n_iframe} bingkai berisi halaman lain. Gabungan yang "
                   f"patut dicurigai.",
                   ikut_diredam=True)
        elif n_iframe >= 3:
            tambah(0.50, "Banyak bingkai tersembunyi",
                   f"Ditemukan {n_iframe} bingkai tersembunyi. Jumlah sebanyak "
                   f"ini tidak lazim untuk halaman biasa.",
                   ikut_diredam=True)
        else:
            tambah(0.20, "Ada bingkai tersembunyi",
                   f"Ditemukan {n_iframe} bingkai tersembunyi. Ini WAJAR pada "
                   f"situs besar (dipakai untuk analitik dan iklan), jadi "
                   f"dicatat saja tanpa dianggap tanda bahaya.",
                   ikut_diredam=True)

    # ---------- Banyak kata kredensial tanpa kolom sandi ----------
    if kata_kredensial >= 4 and not ada_sandi:
        tambah(0.45, "Banyak istilah data rahasia",
               f"Halaman menyebut {kata_kredensial} istilah seperti PIN, OTP, "
               f"atau verifikasi. Perlu diperiksa lebih teliti sebelum "
               f"mengisi apa pun.")

    return temuan


def ringkasan_bukti(bukti: dict[str, Any]) -> list[dict]:
    """
    Susun bukti netral untuk ditampilkan apa adanya - termasuk yang
    menenangkan, bukan hanya yang menakutkan.

    Pengguna berhak melihat dasar kesimpulannya, bukan cuma vonisnya.
    """
    baris: list[dict] = []

    def catat(label: str, nilai, satuan: str = ""):
        if nilai is not None and nilai != "":
            baris.append({"label": label, "nilai": f"{nilai}{satuan}"})

    umur = bukti.get("umur_domain_hari")
    if umur is not None:
        tahun = umur / 365
        umur_teks = f"{umur} hari" + (f" (~{tahun:.1f} tahun)" if tahun >= 1 else "")
        catat("Umur domain", umur_teks)
    catat("Terdaftar sejak", bukti.get("tanggal_dibuat"))
    catat("Negara pendaftaran", bukti.get("negara_pendaftar"))
    catat("Registrar", bukti.get("registrar"))
    catat("Alamat IP", bukti.get("ip"))
    catat("Negara server", bukti.get("negara_hosting"))
    catat("Penyedia hosting", bukti.get("isp"))

    if bukti.get("ssl_ada") is not None:
        if bukti["ssl_ada"] and bukti.get("ssl_cocok_domain"):
            catat("Sertifikat SSL", f"Sah, diterbitkan {bukti.get('ssl_penerbit') or 'pihak tepercaya'}")
        elif bukti["ssl_ada"]:
            catat("Sertifikat SSL", "Ada, tapi tidak cocok dengan alamatnya")
        else:
            catat("Sertifikat SSL", "Tidak ada (sambungan tidak terenkripsi)")

    catat("Status halaman", bukti.get("status_http"))
    if bukti.get("jumlah_pengalihan"):
        catat("Pengalihan saat diklik", f"{bukti['jumlah_pengalihan']} kali")
    catat("Alamat akhir", (bukti.get("url_akhir") or "")[:90])
    catat("Judul halaman", (bukti.get("judul_halaman") or "")[:90])

    if bukti.get("halaman_terbaca"):
        catat("Kolom isian sandi", "Ada" if bukti.get("ada_kolom_sandi") else "Tidak ada")
        catat("Jumlah formulir", bukti.get("jumlah_form"))

    return baris
