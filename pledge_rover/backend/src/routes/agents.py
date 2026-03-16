from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class TriggerRequest(BaseModel):
    filing_text: str

@router.post("/trigger")
async def trigger_council(request: TriggerRequest):
    # In a real app this would call run_council and save to db asynchronously
    # from src.agents.council import run_council
    # result = await run_council(request.filing_text)
    
    return {
        "status": "processing",
        "message": "The Council of Experts has been mobilized to analyze the filing.",
        # "result": result
    }
