from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.scan import DashboardStatsResponse, RecentScansResponse
from app.services.scan_service import get_dashboard_stats, get_recent_scans

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
def dashboard_stats(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Statistik milik akun yang sedang masuk saja."""
    return get_dashboard_stats(db, user.id)


@router.get("/recent", response_model=RecentScansResponse)
def recent_scans(
    limit: int = 10,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Riwayat scan milik akun yang sedang masuk saja.

    Sengaja TIDAK menerima parameter user_id dari luar. Kalau id pemiliknya
    boleh dikirim lewat URL, siapa pun bisa mengganti angkanya dan membaca
    riwayat orang lain. Pemiliknya selalu diambil dari token.
    """
    return get_recent_scans(db, user.id, limit)
