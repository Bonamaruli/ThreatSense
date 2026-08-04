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

from ml.predict import predict_url  # noqa: E402
from ml.predict_email import predict_email  # noqa: E402

from app.models.threat import ScanHistory
from app.schemas.scan import (
    UrlScanRequest, UrlScanResponse,
    EmailScanRequest, EmailScanResponse,
    FileScanRequest, FileScanResponse,
    DashboardStatsResponse, RecentScansResponse,
    ScanResultBase,
)

# ============================================================
# LOGIKA SEMENTARA - TINGGAL UNTUK FILE SCANNER
# ============================================================
# URL Scanner   -> ml/predict.py        (selesai)
# Email Scanner -> ml/predict_email.py  (selesai)
# File Scanner  -> masih memakai dua fungsi di bawah
#
# Dua fungsi ini hanya menebak dari kata kunci pada NAMA berkas, tidak
# membuka isinya sama sekali. Hasilnya BELUM boleh dipakai sebagai temuan
# di laporan.
def dummy_extract_features(input_val: str, scan_type: str) -> dict:
    return {"input": input_val, "type": scan_type, "length": len(input_val)}

def dummy_predict(features: dict) -> tuple[float, str]:
    """Tebakan kasar berbasis kata kunci untuk email & file."""
    text = features.get("input", "").lower()
    if any(kw in text for kw in ["login", "bank", "secure", "verify", "phishing"]):
        return 0.85, "Malicious"
    elif len(text) > 150:
        return 0.55, "Suspicious"
    return 0.10, "Safe"


# === CORE SERVICE FUNCTIONS ===
def process_url_scan(db: Session, req: UrlScanRequest, user_id=None) -> UrlScanResponse:
    """
    Pindai URL memakai mesin penilaian asli (ml/predict.py).

    Mesin itu menggabungkan tiga lapisan: daftar putih situs populer,
    aturan yang bisa dibaca manusia, dan model machine learning yang hanya
    didengar saat dia yakin. Penjelasan lengkap alasannya ada di docstring
    ml/predict.py.
    """
    hasil = predict_url(req.url)

    record = ScanHistory(
        id=uuid.uuid4(), user_id=user_id, scan_type="url", input_value=req.url,
        risk_score=hasil["risk_score"], threat_label=hasil["threat_label"],
        features_json=hasil["features"],
        explanations=hasil["explanations"],
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
    features = dummy_extract_features(filename, "file")
    features["file_size"] = len(file_bytes)
    risk_score, threat_label = dummy_predict(features)

    record = ScanHistory(
        id=uuid.uuid4(), user_id=user_id, scan_type="file", input_value=filename,
        risk_score=risk_score, threat_label=threat_label,
        features_json=features, shap_values={}
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