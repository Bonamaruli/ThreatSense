from fastapi import APIRouter

router = APIRouter()

@router.get("/email")
async def scan_email(email_content: str):
    """
    Endpoint untuk scan email
    """
    return {
        "status": "success",
        "message": "Email scan endpoint ready",
        "risk_score": 0.0,
        "threat_label": "safe"
    }