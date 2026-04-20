"""
Analyze route — LangGraph portfolio intelligence run.
POST /api/analyze  →  runs the 10-node parallel graph and returns structured report.
"""
import os
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
from src.market_rover_graph import create_market_rover_graph
from src.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Graph is compiled once at import time (not per-request)
_graph = create_market_rover_graph()


class AnalysisRequest(BaseModel):
    tickers: List[str]
    discoverable_handle: str


@router.post("")
async def analyze_portfolio(request: AnalysisRequest):
    """
    Runs the LangGraph intelligence pipeline for the given tickers.

    Flow: retrieval -> strategy -> [sentiment, technicals, traditional,
          dividend, sector, forensic] -> shadow -> reporting
    """
    try:
        initial_state = {
            "tickers":              request.tickers,
            "discoverable_handle":  request.discoverable_handle,
            "session_id":           "session_" + os.urandom(8).hex(),
            "celebrations":         [],
            "feedback_prompts":     [],
            "sentiment_data":       [],
            "technical_data":       [],
            "traditional_insights": [],
            "dividend_data":        [],
            "sector_data":          [],
            "errors":               []
        }
        config = {"configurable": {"thread_id": request.discoverable_handle}}
        final_state = await _graph.ainvoke(initial_state, config)
        return final_state

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})
