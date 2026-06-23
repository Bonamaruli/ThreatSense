from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import datetime


# ============== REQUEST SCHEMAS ==============

class URLScanRequest(BaseModel):
    """Schema untuk request scan URL"""
    url: str = Field(..., description="URL yang akan discan")
    
    class Config:
        json_schema_extra = {
            "example": {"url": "https://example.com"}
        }


class EmailScanRequest(BaseModel):
    """Schema untuk request scan email"""
    email_content: str = Field(..., description="Konten email yang akan discan")
    sender_email: Optional[str] = Field(None, description="Email pengirim")
    subject: Optional[str] = Field(None, description="Subjek email")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email_content": "Isi email yang mencurigakan...",
                "sender_email": "suspicious@example.com",
                "subject": "Urgent: Verify Your Account"
            }
        }


class FileScanRequest(BaseModel):
    """Schema untuk request scan file (metadata)"""
    filename: str = Field(..., description="Nama file yang diupload")
    file_size: Optional[int] = Field(None, description="Ukuran file dalam bytes")
    content_type: Optional[str] = Field(None, description="Tipe konten file")


# ============== RESPONSE SCHEMAS ==============

class ScanResponse(BaseModel):
    """Schema umum untuk response scan"""
    status: str = Field(..., description="Status operasi (success/error)")
    message: str = Field(..., description="Pesan hasil scan")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Skor risiko 0-100")
    threat_label: str = Field(..., description="Label ancaman (safe/suspicious/dangerous)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Scan completed",
                "risk_score": 15.5,
                "threat_label": "safe"
            }
        }


class URLScanResponse(ScanResponse):
    """Schema untuk response scan URL"""
    url: str = Field(..., description="URL yang discan")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "URL analysis completed",
                "url": "https://example.com",
                "risk_score": 10.0,
                "threat_label": "safe"
            }
        }


class EmailScanResponse(ScanResponse):
    """Schema untuk response scan email"""
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Email analysis completed",
                "risk_score": 25.0,
                "threat_label": "safe"
            }
        }


class FileScanResponse(ScanResponse):
    """Schema untuk response scan file"""
    filename: str = Field(..., description="Nama file yang discan")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "File analysis completed",
                "filename": "document.pdf",
                "risk_score": 5.0,
                "threat_label": "safe"
            }
        }


class ScanHistoryResponse(BaseModel):
    """Schema untuk response history scan"""
    id: int
    scan_type: str
    input_value: str
    risk_score: float
    threat_label: str
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "scan_type": "url",
                "input_value": "https://example.com",
                "risk_score": 10.0,
                "threat_label": "safe",
                "created_at": "2024-01-01T12:00:00Z"
            }
        }


class DashboardStatsResponse(BaseModel):
    """Schema untuk response dashboard statistics"""
    totalScan: int = Field(..., description="Total semua scan")
    ancamanTerdeteksi: int = Field(..., description="Jumlah ancaman terdeteksi")
    scanAman: int = Field(..., description="Jumlah scan aman")
    scanBerbahaya: int = Field(..., description="Jumlah scan berbahaya")
    
    class Config:
        json_schema_extra = {
            "example": {
                "totalScan": 150,
                "ancamanTerdeteksi": 25,
                "scanAman": 100,
                "scanBerbahaya": 25
            }
        }


class ErrorResponse(BaseModel):
    """Schema untuk response error"""
    status: str = "error"
    message: str
    detail: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "message": "Invalid input",
                "detail": "URL format tidak valid"
            }
        }
