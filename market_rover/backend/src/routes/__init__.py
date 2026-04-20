"""
Modular routes package for the Market-Rover API.
Each sub-router handles a discrete domain:
  - auth    : Google OAuth flow
  - analyze : LangGraph portfolio intelligence run
  - profile : User persona (Sleep Test + CRUD)
  - forecast: Historical stance tracker
  - shadow  : Institutional shadow signals (ACCUMULATION / DISTRIBUTION)
  - calendar: Muhurtham windows + seasonal patterns
  - heatmap : Monthly returns matrix via yfinance
"""
from fastapi import APIRouter
from src.routes.auth import router as auth_router
from src.routes.analyze import router as analyze_router
from src.routes.profile import router as profile_router
from src.routes.forecast import router as forecast_router
from src.routes.shadow import router as shadow_router
from src.routes.calendar import router as calendar_router
from src.routes.heatmap import router as heatmap_router

router = APIRouter()
router.include_router(auth_router,    prefix="/auth",     tags=["Authentication"])
router.include_router(analyze_router, prefix="/analyze",  tags=["Intelligence"])
router.include_router(profile_router, prefix="/profile",  tags=["Profile"])
router.include_router(forecast_router,prefix="/forecasts",tags=["Forecasts"])
router.include_router(shadow_router,  prefix="/shadow",   tags=["Shadow"])
router.include_router(calendar_router,prefix="/calendar", tags=["Calendar"])
router.include_router(heatmap_router, prefix="/heatmap",  tags=["Heatmap"])
