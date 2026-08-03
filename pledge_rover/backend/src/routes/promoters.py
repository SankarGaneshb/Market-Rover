from fastapi import APIRouter, HTTPException
from typing import List
from sqlalchemy import select
from ..config.database import async_session
from ..data.models import Promoter
from pydantic import BaseModel

router = APIRouter()

class PromoterResponse(BaseModel):
    symbol: str
    company_name: str
    governance_score: float = 5.0
    total_shares: float = 0.0
    holding_pct: float = 0.0
    pledged_pct: float = 0.0
    skin_in_the_game: float = 0.0
    skin_layer1: float = 0.0
    skin_layer2: float = 0.0
    survival_score: float = 0.0
    intent_label: str = "Neutral"
    trust_signal: str = "Stable"
    release_create_ratio: float = 1.0
    risk: str = "Medium"

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

        # Dynamic Risk Calculation
        if promoter.pledged_pct > 25 or (promoter.governance_score < 4.0 and promoter.governance_score > 0):
            promoter.risk = "High"
        elif promoter.pledged_pct < 5 and promoter.governance_score > 7.0:
            promoter.risk = "Low"
        else:
            promoter.risk = "Medium"

        return promoter

@router.get("/", response_model=List[PromoterResponse])
async def list_promoters():
    async with async_session() as session:
        stmt = select(Promoter)
        result = await session.execute(stmt)
        promoters = result.scalars().all()

        for p in promoters:
            if p.pledged_pct > 25 or (p.governance_score < 4.0 and p.governance_score > 0):
                p.risk = "High"
            elif p.pledged_pct < 5 and p.governance_score > 7.0:
                p.risk = "Low"
            else:
                p.risk = "Medium"
        return promoters
