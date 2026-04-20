"""
Shadow route — dedicated institutional signals endpoint.
GET /api/shadow/{user_handle}        → user's historical shadow signals
GET /api/shadow/market               → live cross-ticker shadow scan summary
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from src.utils.db_manager import db
from src.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/market")
async def get_market_shadow():
    """
    Returns the latest cross-user shadow signals: ACCUMULATION and DISTRIBUTION
    tickers ranked by recency. Drives the Shadow Discovery tab live feed.
    """
    try:
        await db.connect()
        query = """
            SELECT ticker, stance, logic_summary, analysis_date, user_id
            FROM public.agent_memory_ltm
            WHERE stance IN ('ACCUMULATION', 'DISTRIBUTION', 'WARNING')
            ORDER BY analysis_date DESC
            LIMIT 20
        """
        async with db.pool.acquire() as conn:
            rows = await conn.fetch(query)

        result = []
        for r in rows:
            item = dict(r)
            if item.get("analysis_date"):
                item["analysis_date"] = item["analysis_date"].isoformat()
            result.append(item)

        return result
    except Exception as e:
        logger.error(f"get_market_shadow failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/{user_handle}")
async def get_user_shadow(user_handle: str):
    """
    Returns all shadow/forensic signals generated for the given user,
    filtered to ACCUMULATION and DISTRIBUTION stances only.
    """
    try:
        await db.connect()
        query = """
            SELECT ticker, stance, logic_summary, analysis_date
            FROM public.agent_memory_ltm
            WHERE user_id = $1
              AND stance IN ('ACCUMULATION', 'DISTRIBUTION', 'WARNING')
            ORDER BY analysis_date DESC
        """
        async with db.pool.acquire() as conn:
            rows = await conn.fetch(query, user_handle)

        result = []
        for r in rows:
            item = dict(r)
            if item.get("analysis_date"):
                item["analysis_date"] = item["analysis_date"].isoformat()
            result.append(item)

        return result
    except Exception as e:
        logger.error(f"get_user_shadow failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
