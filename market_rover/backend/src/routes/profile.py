"""
Profile routes — Investor persona (Sleep Test + CRUD).
Extracted from server.py /api/profile* endpoints.
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from src.utils.db_manager import db
from src.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class ProfileUpdateRequest(BaseModel):
    user_handle: str
    persona: str


class PersonaAnalysisRequest(BaseModel):
    q1: int  # 1=Conservative, 3=Aggressive
    q2: int
    q3: int


@router.post("")
async def update_profile(request: ProfileUpdateRequest):
    """Save / update the user's investor persona."""
    try:
        await db.connect()
        await db.set_user_persona(request.user_handle, request.persona)
        return {"status": "success", "persona": request.persona}
    except Exception as e:
        logger.error(f"update_profile failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/{user_handle}")
async def get_profile(user_handle: str):
    """Retrieve the user's saved persona."""
    try:
        await db.connect()
        persona = await db.get_user_persona(user_handle)
        return {"user_handle": user_handle, "persona": persona or "Not Set"}
    except Exception as e:
        logger.error(f"get_profile failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/analyze")
async def analyze_persona(request: PersonaAnalysisRequest):
    """
    Calibrates Investor Persona from the 3-question Sleep Test scores.

    Scoring:
      3-4  -> The Preserver  (most conservative)
      5-6  -> The Defender
      7    -> The Compounder
      8-9  -> The Hunter     (most aggressive)
    """
    total = request.q1 + request.q2 + request.q3
    if total <= 4:
        persona = "The Preserver"
    elif total <= 6:
        persona = "The Defender"
    elif total <= 7:
        persona = "The Compounder"
    else:
        persona = "The Hunter"

    return {"persona": persona, "score": total}
