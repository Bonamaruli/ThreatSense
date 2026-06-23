from fastapi import APIRouter

router = APIRouter()

@router.get("/url")
async def scan_url(url: str):
    """
    Endpoint untuk scan URL
    """
    return {
        "status": "success",
        "message": "URL scan endpoint ready",
        "url": url,
        "risk_score": 0.0,
        "threat_label": "safe"
    }