from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel

router = APIRouter()

class PromoterResponse(BaseModel):
    symbol: str
    company_name: str
    governance_score: float
    total_shares: float

# Mock DB return for frontend testing
MOCK_PROMOTERS = [
    {"symbol": "LLOYDSME", "company_name": "Lloyds Metals And Energy Limited", "governance_score": 3.8, "total_shares": 504.6},
    {"symbol": "DEEPAKFERT", "company_name": "Deepak Fertilizers And Petrochemicals", "governance_score": 6.2, "total_shares": 126.9},
    {"symbol": "NOCIL", "company_name": "NOCIL Limited", "governance_score": 8.5, "total_shares": 166.6},
    {"symbol": "AJANTPHARM", "company_name": "Ajanta Pharma", "governance_score": 9.1, "total_shares": 126.0},
    {"symbol": "CAMLINFINE", "company_name": "Camlin Fine Sciences", "governance_score": 4.5, "total_shares": 167.5}
]

@router.get("/{symbol}", response_model=PromoterResponse)
async def get_promoter(symbol: str):
    promoter = next((p for p in MOCK_PROMOTERS if p["symbol"] == symbol.upper()), None)
    if not promoter:
        raise HTTPException(status_code=404, detail="Promoter not found")
    return promoter

@router.get("/", response_model=List[PromoterResponse])
async def list_promoters():
    return MOCK_PROMOTERS
