from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime

class UrlScanRequest(BaseModel):
    url: str = Field(..., description="URL yang akan discan")

class EmailScanRequest(BaseModel):
    email_content: str = Field(..., description="Isi lengkap email yang akan discan")

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