from fastapi import APIRouter
from datetime import datetime
import pytz

router = APIRouter()

def get_ist_date_string():
    ist = pytz.timezone('Asia/Kolkata')
    return datetime.now(ist).isoformat()

@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "Pledge Rover API",
        "version": "1.0.0",
        "timestamp": get_ist_date_string()
    }
