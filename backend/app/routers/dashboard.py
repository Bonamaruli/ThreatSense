from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.threat import ScanHistory

router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Get dashboard statistics
    """
    total_scan = db.query(ScanHistory).count()
    
    ancaman = db.query(ScanHistory).filter(
        ScanHistory.risk_score >= 70
    ).count()
    
    aman = db.query(ScanHistory).filter(
        ScanHistory.risk_score < 30
    ).count()
    
    berbahaya = db.query(ScanHistory).filter(
        ScanHistory.risk_score >= 70
    ).count()
    
    return {
        "totalScan": total_scan,
        "ancamanTerdeteksi": ancaman,
        "scanAman": aman,
        "scanBerbahaya": berbahaya
    }

@router.get("/recent-scans")
async def get_recent_scans(limit: int = 10, db: Session = Depends(get_db)):
    """
    Get recent scan history
    """
    scans = db.query(ScanHistory).order_by(
        ScanHistory.created_at.desc()
    ).limit(limit).all()
    
    return [
        {
            "id": scan.id,
            "scan_type": scan.scan_type,
            "input_value": scan.input_value,
            "risk_score": scan.risk_score,
            "threat_label": scan.threat_label,
            "created_at": scan.created_at
        }
        for scan in scans
    ]