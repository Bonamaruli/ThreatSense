"""
jaringan_aman.py
================
Penjaga agar pemindai tidak bisa dipaksa membuka alamat INTERNAL.

KERENTANAN YANG DITUTUP DI SINI: SSRF
-------------------------------------
Pemindaian mendalam membuka alamat apa pun yang diketik pengguna. Tanpa
penjagaan, siapa pun bisa memakai server ThreatSense sebagai perantara
untuk menjangkau tempat yang seharusnya tidak bisa mereka capai:

    http://127.0.0.1:8000/          -> layanan internal di server itu sendiri
    http://192.168.1.1/             -> perangkat di jaringan lokal
    http://169.254.169.254/         -> di layanan cloud, alamat ini
                                       mengembalikan kunci akses server

Terbukti nyata saat pengujian: memindai "http://127.0.0.1:8000/health"
berhasil dan mengembalikan status 200. Jadi server bisa dipakai memetakan
jaringan internal dari luar - kelemahan yang namanya Server-Side Request
Forgery (SSRF).

CARA MENJAGANYA
---------------
Nama domain diterjemahkan dulu jadi alamat IP, LALU alamat itu diperiksa.
Memeriksa nama saja tidak cukup: penyerang bisa mendaftarkan domain biasa
yang diarahkan ke 127.0.0.1, dan namanya akan terlihat wajar.

Pemeriksaan diulang setelah setiap pengalihan, karena alamat luar yang
tampak wajar bisa mengalihkan ke alamat internal di langkah berikutnya.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


class AlamatDitolak(Exception):
    """Alamat menunjuk ke jaringan internal dan tidak boleh dibuka."""


# Skema selain http/https tidak pernah diikuti. file:// bisa membaca berkas
# di server, gopher:// dan dict:// bisa dipakai mengirim perintah ke layanan
# internal - semuanya jalur SSRF yang sudah dikenal.
SKEMA_DIIZINKAN = {"http", "https"}

# Port yang jelas bukan layanan web umum. Membatasi port mempersempit
# ruang gerak pemindaian jaringan internal.
PORT_DIIZINKAN = {80, 443, 8000, 8080, 8443, 3000, 5000}


def _ip_internal(ip: ipaddress._BaseAddress) -> bool:
    """
    Benarkah alamat ini menunjuk ke jaringan internal?

    Dipakai pustaka bawaan Python, bukan daftar tulisan tangan, supaya
    rentang yang jarang diingat pun ikut tertutup - misalnya IPv6 lokal
    dan alamat yang dipetakan dari IPv4.
    """
    return (
        ip.is_private          # 10.x, 172.16-31.x, 192.168.x
        or ip.is_loopback      # 127.x
        or ip.is_link_local    # 169.254.x - alamat metadata cloud
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def periksa_alamat(url: str) -> str:
    """
    Pastikan sebuah alamat aman dibuka. Kembalikan alamat IP-nya.

    Raises:
        AlamatDitolak: bila menunjuk jaringan internal, memakai skema
                       terlarang, atau namanya tidak bisa diterjemahkan.
    """
    p = urlparse(url)

    if p.scheme.lower() not in SKEMA_DIIZINKAN:
        raise AlamatDitolak(
            f"Hanya alamat http dan https yang diperiksa (ditemukan: {p.scheme})"
        )

    host = (p.hostname or "").strip()
    if not host:
        raise AlamatDitolak("Nama host tidak terbaca")

    port = None
    try:
        port = p.port
    except ValueError:
        raise AlamatDitolak("Nomor port tidak sah")

    if port is not None and port not in PORT_DIIZINKAN:
        raise AlamatDitolak(f"Port {port} tidak diizinkan untuk pemeriksaan")

    # Terjemahkan nama jadi IP, LALU periksa IP-nya.
    #
    # Memeriksa nama saja tidak cukup - "situs-biasa.com" bisa saja diarahkan
    # pemiliknya ke 127.0.0.1, dan namanya tidak akan menimbulkan kecurigaan.
    try:
        info = socket.getaddrinfo(host, port or 80, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise AlamatDitolak("Nama domain tidak bisa diterjemahkan")

    if not info:
        raise AlamatDitolak("Nama domain tidak menghasilkan alamat")

    # SEMUA alamat hasil terjemahan harus aman, bukan cuma yang pertama.
    # Satu nama bisa menunjuk beberapa IP sekaligus, dan penyerang bisa
    # menyelipkan satu alamat internal di antaranya.
    for keluarga, _, _, _, sockaddr in info:
        mentah = sockaddr[0]
        try:
            ip = ipaddress.ip_address(mentah)
        except ValueError:
            raise AlamatDitolak(f"Alamat IP tidak sah: {mentah}")

        if _ip_internal(ip):
            raise AlamatDitolak(
                f"Alamat ini menunjuk jaringan internal ({mentah}) dan tidak "
                f"diperiksa demi keamanan server."
            )

    return info[0][4][0]


def aman_dibuka(url: str) -> tuple[bool, str]:
    """Bentuk yang lebih enak dipakai: (aman, alasan bila ditolak)."""
    try:
        periksa_alamat(url)
        return True, ""
    except AlamatDitolak as e:
        return False, str(e)
