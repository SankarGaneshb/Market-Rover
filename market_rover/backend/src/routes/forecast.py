"""
Forecast routes — historical analysis stance tracker.
GET /api/forecasts/{user_handle}
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from src.utils.db_manager import db
from src.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/{user_handle}")
async def get_forecasts(user_handle: str):
    """
    Returns all historical analysis stances for the user as a forecast tracker.
    Sourced from agent_memory_ltm table (written by the reporting_node).
    """
    try:
        await db.connect()
        history = await db.get_forecast_history(user_handle)
        result = [dict(r) for r in history]
        for item in result:
            if item.get("analysis_date"):
                item["analysis_date"] = item["analysis_date"].isoformat()
        return result
    except Exception as e:
        logger.error(f"get_forecasts failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
