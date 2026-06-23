from fastapi import APIRouter, UploadFile, File

router = APIRouter()

@router.post("/file")
async def scan_file(file: UploadFile = File(...)):
    """
    Endpoint untuk scan file
    """
    return {
        "status": "success",
        "message": "File scan endpoint ready",
        "filename": file.filename,
        "risk_score": 0.0,
        "threat_label": "safe"
    }