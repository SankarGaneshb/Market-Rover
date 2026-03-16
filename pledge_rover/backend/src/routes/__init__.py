from fastapi import APIRouter
from src.routes import health, promoters, pledges, agents

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(promoters.router, prefix="/promoters", tags=["Promoters"])
api_router.include_router(pledges.router, prefix="/pledges", tags=["Pledges"])
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
