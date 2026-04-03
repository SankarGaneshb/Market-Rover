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
    """Background task to run the Agentic Council and persist results to SQL."""
    from src.config.database import async_session
    from src.data.models import Promoter, AnalysisRun
    from sqlalchemy import select, update
    import json

    try:
        # 1. Harvest or Mock Filing
        symbol = "LLOYDSME" # Default for mock/feed without explicit symbol
        company_name = "Lloyds Metals And Energy Limited"

        if not filing_text:
            harvester = ExchangeHarvester()
            feed = await harvester.get_7_day_combined_feed()
            if feed:
                f = feed[0]
                symbol = f['symbol']
                company_name = f['company_name']
                filing_text = f"PLEDGE EVENT: {f['symbol']} ({f['company_name']}) - Pledgor: {f.get('promoter_name', 'N/A')}. Percentage: {f['percentage_pledged']}%. Purpose: {f['purpose']}."
            else:
                filing_text = f"BASELINE SCAN: {symbol} ({company_name}) - Checking for off-market shadow entity movements."

        ScanManager.set_status("scanning", f"The Council of Experts is analyzing {symbol}...")
        
        # 2. Run Agentic Suite
        # In a real app, we'd fetch metrics from the DB to ground the agents
        result = await run_council(filing_text)
        
        # 3. Persist Results (SQL Transaction)
        async with async_session() as session:
            async with session.begin():
                # Find the promoter
                stmt = select(Promoter).where(Promoter.symbol == symbol)
                db_result = await session.execute(stmt)
                promoter = db_result.scalars().first()
                
                if not promoter:
                    promoter = Promoter(symbol=symbol, company_name=company_name)
                    session.add(promoter)
                    await session.flush()

                # Update Promoter Governance Score
                promoter.governance_score = result.get("governance_score", 5.0)
                
                # Create Analysis Run
                analysis = AnalysisRun(
                    promoter_id=promoter.id,
                    trigger_source="Manual Pulse Scan",
                    debate_log=result.get("debate_summary", "Detailed debate stored in agent logs."),
                    final_sentiment=result.get("final_sentiment", "Neutral"),
                    governance_score_calc=result.get("governance_score", 5.0)
                )
                session.add(analysis)
            
            await session.commit()

        # 4. Finalize Status
        ScanManager.set_status("idle", f"Scan complete for {symbol}. Governance Score updated to {result.get('governance_score')}.")
    except Exception as e:
        print(f"CRITICAL ERROR in AI Council: {str(e)}")
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
