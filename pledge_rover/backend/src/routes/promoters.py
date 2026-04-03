from fastapi import APIRouter, HTTPException
from typing import List
from sqlalchemy import select
from src.config.database import async_session
from src.data.models import Promoter
from pydantic import BaseModel

router = APIRouter()

class PromoterResponse(BaseModel):
    symbol: str
    company_name: str
    governance_score: float
    total_shares: float
    holding_pct: float
    pledged_pct: float
    skin_in_the_game: float
    skin_layer1: float
    skin_layer2: float
    survival_score: float
    intent_label: str
    trust_signal: str
    release_create_ratio: float

    class Config:
        from_attributes = True

@router.get("/{symbol}", response_model=PromoterResponse)
async def get_promoter(symbol: str):
    async with async_session() as session:
        stmt = select(Promoter).where(Promoter.symbol == symbol.upper())
        result = await session.execute(stmt)
        promoter = result.scalars().first()
        if not promoter:
            raise HTTPException(status_code=404, detail="Promoter not found")
        return promoter

@router.get("/", response_model=List[PromoterResponse])
async def list_promoters():
    async with async_session() as session:
        stmt = select(Promoter)
        result = await session.execute(stmt)
        return result.scalars().all()
