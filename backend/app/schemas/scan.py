import re
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, field_validator

# Alamat dianggap layak dipindai kalau bagian hostname-nya masuk akal:
# ada titik pemisah domain dan akhiran (contoh.com), berupa nomor IP, atau
# localhost. Pemeriksaan ini sengaja longgar - tugasnya cuma menyaring
# masukan yang jelas bukan alamat, bukan menilai apakah situsnya ada.
_POLA_HOST_WAJAR = re.compile(
    r"^(?:"
    r"(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}"   # nama domain
    r"|(?:\d{1,3}\.){3}\d{1,3}"                          # alamat IPv4
    r"|localhost"
    r")$",
    re.IGNORECASE,
)


class UrlScanRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048,
                     description="URL yang akan discan")

    # Pemeriksaan mendalam benar-benar MEMBUKA alamatnya untuk mengambil
    # bukti: umur domain, negara server, sertifikat, ke mana ia mengalihkan,
    # dan isi halamannya.
    #
    # Bawaannya mati karena butuh 2-13 detik (dibanding 0,1 detik untuk
    # pemeriksaan nama). Pengguna yang memilih menyalakannya sudah tahu
    # akan menunggu lebih lama, dan itu keputusan yang pantas ada di tangan
    # mereka - bukan dipaksakan ke semua pemindaian.
    mendalam: bool = Field(
        False,
        description="Buka alamatnya untuk mengambil bukti (lebih lambat)",
    )

    @field_validator("url")
    @classmethod
    def _url_harus_masuk_akal(cls, v: str) -> str:
        """
        Tolak masukan yang jelas bukan alamat, SEBELUM masuk ke mesin
        pemindai.

        Tanpa penyaring ini, masukan seperti "://rusak" atau "!!!" tetap
        diproses dan menghasilkan penilaian yang tidak berarti apa-apa -
        atau, seperti yang sempat terjadi pada "https:google.com", membuat
        seluruh permintaan gagal dengan pesan "kesalahan internal" yang
        tidak menjelaskan apa pun kepada pengguna.
        """
        teks = (v or "").strip().replace(" ", "")
        if not teks:
            raise ValueError("Alamat tidak boleh kosong.")

        # Ambil bagian hostname-nya saja: buang skema, path, query, dan port
        sisa = re.sub(r"^[a-zA-Z][a-zA-Z0-9+.-]*:(?://)?", "", teks)
        host = sisa.split("/")[0].split("?")[0].split("#")[0]
        host = host.split("@")[-1]        # buang bagian pengguna:sandi@
        host = host.split(":")[0]         # buang nomor port

        if not _POLA_HOST_WAJAR.match(host):
            raise ValueError(
                "Alamat tidak dikenali. Contoh yang benar: "
                "https://contoh.com atau contoh.com"
            )

        return teks

class EmailScanRequest(BaseModel):
    # Batas 1 MB. Email sungguhan yang isinya lebih dari itu praktis tidak
    # ada - lampiran tidak ikut ditempel di sini. Tanpa batas, satu
    # permintaan berisi teks puluhan megabyte bisa menghabiskan memori
    # server, dan pencarian pola di dalamnya akan memakan waktu sangat lama.
    email_content: str = Field(
        ..., min_length=1, max_length=1_000_000,
        description="Isi lengkap email yang akan discan (maksimal 1 MB)",
    )

class FileScanRequest(BaseModel):
    filename_hint: Optional[str] = Field(None, description="Opsional: hint nama file asli")

class ScanResultBase(BaseModel):
    id: uuid.UUID
    scan_type: str
    input_value: str
    risk_score: float = Field(..., ge=0.0, le=1.0)
    threat_label: str
    features_json: Dict[str, Any] = {}
    shap_values: Optional[Dict[str, Any]] = None
    # Daftar alasan yang bisa dibaca pengguna. Tiap item berisi
    # {judul, alasan, bobot}.
    explanations: Optional[List[Dict[str, Any]]] = None
    # Bukti hasil pemeriksaan mendalam, hanya terisi kalau mendalam=True.
    # Berisi daftar {label, nilai} siap tampil, contoh:
    #   {"label": "Umur domain", "nilai": "5 hari"}
    evidence_summary: Optional[List[Dict[str, Any]]] = None
    deep_scan: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}

class UrlScanResponse(ScanResultBase):
    scan_type: str = "url"

class EmailScanResponse(ScanResultBase):
    scan_type: str = "email"

class FileScanResponse(ScanResultBase):
    scan_type: str = "file"

class DashboardStatsResponse(BaseModel):
    total_scans: int
    malicious_detected: int
    safe_detected: int
    suspicious_detected: int

class RecentScansResponse(BaseModel):
    scans: List[ScanResultBase]