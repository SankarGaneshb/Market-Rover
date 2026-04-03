import asyncio
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from src.data.scan_manager import ScanManager
from src.agents.council import run_council
from src.agents.harvester import ExchangeHarvester

router = APIRouter()

class TriggerRequest(BaseModel):
    filing_text: str = None # Optional, if none, scan recent BSE/NSE feed

async def perform_scan_background(filing_text: str = None):
    """Background task to run the Agentic Council."""
    try:
        # If no filing provided, find a real one from the Harvester
        if not filing_text:
            harvester = ExchangeHarvester()
            feed = await harvester.get_7_day_combined_feed()
            if feed:
                # Pick the top one (likely most critical)
                f = feed[0]
                filing_text = f"PLEDGE EVENT: {f['symbol']} ({f['company_name']}) - Pledgor: {f.get('promoter_name', 'N/A')}. Percentage: {f['percentage_pledged']}%. Purpose: {f['purpose']}."
            else:
                filing_text = "MOCK FILING: No recent filings found in 7-day feed. Using baseline scan."

        ScanManager.set_status("scanning", "The Council of Experts is analyzing recent market filings...")
        
        # In a real app, we'd fetch metrics from src.data.mock_historical or a real DB
        # For now, simulate a complex analysis
        await run_council(filing_text)
        
        # After analysis, mark as idle
        ScanManager.set_status("idle", "Scan complete. Dashboard updated.")
    except Exception as e:
        ScanManager.set_status("idle", f"Scan failed: {str(e)}")

@router.post("/trigger")
async def trigger_council(request: TriggerRequest, background_tasks: BackgroundTasks):
    """Manually trigger the AI Council scan process."""
    if ScanManager.is_scanning():
        return {"status": "scanning", "message": "An active scan is already in progress."}
    
    # Set to scanning first
    ScanManager.set_status("scanning", "Scanning for latest information...")
    
    # Run the heavy agentic pipeline in background
    background_tasks.add_task(perform_scan_background, request.filing_text)
    
    return {
        "status": "scanning",
        "message": "Scanning for latest information...",
        "eta": "The Council usually resolves in 15-30 seconds."
    }

@router.get("/status")
async def get_scan_status():
    """Retrieve the current persistent scan state."""
    return ScanManager.get_state()
