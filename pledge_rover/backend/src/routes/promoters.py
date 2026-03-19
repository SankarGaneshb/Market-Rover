from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
from src.data.mock_historical import get_all_enriched_promoters, get_enriched_promoter_data

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

@router.get("/{symbol}", response_model=PromoterResponse)
async def get_promoter(symbol: str):
    promoter = get_enriched_promoter_data(symbol)
    if not promoter:
        raise HTTPException(status_code=404, detail="Promoter not found")
    return promoter

@router.get("/", response_model=List[PromoterResponse])
async def list_promoters():
    return get_all_enriched_promoters()
