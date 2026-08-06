import sys
import os
import uuid
from sqlalchemy.orm import Session

# ============================================================
# PENTING: Registrasi path folder root ke sys.path
# ============================================================
# scan_service.py ada di: backend/app/services/
# url_features.py ada di: ml/features/  (SEJAJAR dengan backend/, bukan di dalamnya)
#
# Karena uvicorn dijalankan dari dalam folder backend/, Python defaultnya
# hanya "melihat" ke dalam backend/. Baris di bawah ini menambahkan folder
# root project (satu level di atas backend/) ke sys.path, supaya Python
# bisa menemukan folder ml/ juga.
_current_file = os.path.abspath(__file__)                          # .../backend/app/services/scan_service.py
_backend_dir = os.path.abspath(os.path.join(_current_file, "..", "..", ".."))  # .../backend
_project_root = os.path.abspath(os.path.join(_backend_dir, ".."))  # .../ThreatSense (root)

if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from ml.scoring.url import predict_url  # noqa: E402
from ml.scoring.file import predict_file  # noqa: E402
from ml.scoring.email import predict_email  # noqa: E402

from app.models.threat import ScanHistory
from app.schemas.scan import (
    UrlScanRequest, UrlScanResponse,
    EmailScanRequest, EmailScanResponse,
    FileScanRequest, FileScanResponse,
    DashboardStatsResponse, RecentScansResponse,
    ScanResultBase,
)

# ============================================================
# MESIN PENILAIAN - ketiganya sudah memakai analisis asli
# ============================================================
# URL Scanner   -> ml/predict.py        (nama domain + bukti dari membuka
#                                        alamatnya + model machine learning)
# Email Scanner -> ml/predict_email.py  (header + isi surat)
# File Scanner  -> ml/predict_file.py   (analisis statis isi berkas)
#
# Dua fungsi tebakan lama (dummy_extract_features dan dummy_predict) sudah
# dihapus. Keduanya hanya membaca kata kunci pada teks masukan dan tidak
# pernah membuka isi sebenarnya - menyisakannya di sini hanya akan
# menggoda orang untuk memakainya lagi.


# === CORE SERVICE FUNCTIONS ===
def process_url_scan(db: Session, req: UrlScanRequest, user_id=None) -> UrlScanResponse:
    """
    Pindai URL memakai mesin penilaian asli (ml/predict.py).

    Mesin itu menggabungkan tiga lapisan: daftar putih situs populer,
    aturan yang bisa dibaca manusia, dan model machine learning yang hanya
    didengar saat dia yakin. Penjelasan lengkap alasannya ada di docstring
    ml/predict.py.
    """
    mendalam = getattr(req, "mendalam", False)

    # Ambil hasil pemeriksaan domain yang sudah pernah disimpan, supaya
    # WHOIS tidak dipanggil berulang untuk domain yang sama. Hanya bagian
    # stabil yang dipakai ulang - isi halaman selalu diambil segar.
    cache_domain = None
    if mendalam:
        from app.services import cache_service
        from ml.scoring.url import _domain_terdaftar

        nama_domain = _domain_terdaftar(req.url)
        cache_domain = cache_service.ambil(db, nama_domain)

    hasil = predict_url(req.url, mendalam=mendalam, cache_domain=cache_domain)

    # Simpan hasil baru untuk dipakai pemindaian berikutnya
    if mendalam and hasil.get("evidence") and not cache_domain:
        cache_service.simpan(db, nama_domain, hasil["evidence"])

    record = ScanHistory(
        id=uuid.uuid4(), user_id=user_id, scan_type="url", input_value=req.url,
        risk_score=hasil["risk_score"], threat_label=hasil["threat_label"],
        features_json=hasil["features"],
        explanations=hasil["explanations"],
        evidence_summary=hasil.get("evidence_summary") or None,
        deep_scan=bool(hasil.get("deep_scan")),
        # shap_values menyimpan angka mentah dari model, dipisah dari
        # explanations yang berisi kalimat untuk dibaca pengguna.
        shap_values={
            "ml_score": hasil["ml_score"],
            "rules_fired": hasil["rules_fired"],
            "whitelisted": hasil["whitelisted"],
        },
        # created_at sengaja TIDAK diisi di sini — biarkan database yang
        # mengisi lewat server_default=func.now(). Jam server database jadi
        # satu-satunya acuan waktu, jadi tidak ada selisih jam antara
        # aplikasi dan database.
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return UrlScanResponse.model_validate(record)

def process_email_scan(db: Session, req: EmailScanRequest, user_id=None) -> EmailScanResponse:
    """
    Pindai email memakai mesin penilaian asli (ml/predict_email.py).

    Mesin itu memeriksa dua sisi: aturan terhadap header dan isi email,
    plus menilai setiap tautan di dalamnya memakai mesin URL yang sudah
    selesai dibuat.
    """
    hasil = predict_email(req.email_content)

    record = ScanHistory(
        id=uuid.uuid4(), user_id=user_id, scan_type="email",
        # Hanya cuplikan yang disimpan. Isi email adalah data pribadi -
        # tidak ada alasan menyimpannya utuh hanya untuk riwayat pemindaian.
        input_value=req.email_content[:200],
        risk_score=hasil["risk_score"], threat_label=hasil["threat_label"],
        features_json=hasil["features"],
        explanations=hasil["explanations"],
        shap_values={
            "rules_fired": hasil["rules_fired"],
            "link_results": hasil["link_results"],
        },
        # created_at sengaja TIDAK diisi di sini — biarkan database yang
        # mengisi lewat server_default=func.now(). Jam server database jadi
        # satu-satunya acuan waktu, jadi tidak ada selisih jam antara
        # aplikasi dan database.
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return EmailScanResponse.model_validate(record)

def process_file_scan(db: Session, filename: str, file_bytes: bytes, req: FileScanRequest = None, user_id=None) -> FileScanResponse:
    """
    Pindai berkas dengan analisis statis.

    Berkasnya TIDAK PERNAH dijalankan - hanya dibaca sebagai data. Yang
    diperiksa adalah isi sebenarnya (magic bytes), kecocokan dengan
    ekstensinya, keberadaan makro, dan pola berbahaya di dalam PDF.

    Sebelumnya bagian ini cuma menebak dari nama berkas dan ukurannya,
    sehingga "virus.exe" yang diganti nama jadi "faktur.pdf" lolos begitu
    saja - sekarang justru itulah yang paling cepat tertangkap.
    """
    hasil = predict_file(filename, file_bytes)

    record = ScanHistory(
        id=uuid.uuid4(), user_id=user_id, scan_type="file", input_value=filename,
        risk_score=hasil["risk_score"], threat_label=hasil["threat_label"],
        features_json=hasil["features"],
        explanations=hasil["explanations"],
        evidence_summary=hasil["evidence_summary"],
        shap_values={"rules_fired": hasil["rules_fired"]}
        # created_at sengaja TIDAK diisi di sini — biarkan database yang
        # mengisi lewat server_default=func.now(). Jam server database jadi
        # satu-satunya acuan waktu, jadi tidak ada selisih jam antara
        # aplikasi dan database.
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return FileScanResponse.model_validate(record)

def get_dashboard_stats(db: Session, user_id) -> DashboardStatsResponse:
    """
    Hitung statistik HANYA untuk akun yang sedang masuk.

    user_id wajib diisi, tidak boleh None. Kalau parameternya dibuat opsional,
    sekali saja pemanggilnya lupa mengisi, statistik SELURUH pengguna akan
    ikut terhitung - kebocoran data antar akun yang tidak memunculkan error
    apa pun sehingga sulit disadari.
    """
    dasar = db.query(ScanHistory).filter(ScanHistory.user_id == user_id)

    def hitung(label):
        return dasar.filter(ScanHistory.threat_label == label).count()

    return DashboardStatsResponse(
        total_scans=dasar.count(),
        malicious_detected=hitung("Malicious"),
        safe_detected=hitung("Safe"),
        suspicious_detected=hitung("Suspicious"),
    )


def get_recent_scans(db: Session, user_id, limit: int = 10) -> RecentScansResponse:
    """Riwayat terakhir milik akun yang sedang masuk."""
    # Batas atas dipasang supaya permintaan ?limit=999999 tidak menarik
    # seluruh isi tabel sekaligus.
    limit = max(1, min(limit, 100))

    scans = (
        db.query(ScanHistory)
        .filter(ScanHistory.user_id == user_id)
        .order_by(ScanHistory.created_at.desc())
        .limit(limit)
        .all()
    )
    return RecentScansResponse(scans=[ScanResultBase.model_validate(s) for s in scans])