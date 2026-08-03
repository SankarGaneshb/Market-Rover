from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import date, timedelta
import random
from .models import RightsIssue, RightsIssueDetails, RightsIssueTimeline, PaymentSchedule, RetailAllocationRules
from .calculations import (
    calculate_terp,
    calculate_re_intrinsic_value,
    calculate_subscription_pl,
    calculate_additional_allotment_probability
)
from .orchestrator import run_ownerise_audit
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["ownerise"])

# Dummy database for initial implementation phase
MOCK_RIGHTS_ISSUES = {
    "RELIANCE": RightsIssue(
        details=RightsIssueDetails(
            symbol="RELIANCE",
            company_name="Reliance Industries Ltd.",
            base_issue_size_crores=53124.20,
            old_shares_ratio=15,
            new_shares_ratio=1,
            issue_price=1257.0,
            current_market_price=1450.0
        ),
        timeline=RightsIssueTimeline(
            announcement_date=date(2020, 4, 30),
            record_date=date(2020, 5, 14),
            open_date=date(2020, 5, 20),
            renunciation_date=date(2020, 5, 29),
            close_date=date(2020, 6, 3),
            allotment_date=date(2020, 6, 10),
            listing_date=date(2020, 6, 15)
        ),
        payment_schedule=PaymentSchedule(
            is_partly_paid=True,
            ticker_symbol="RELIANCE-PP",
            installments=[]
        ),
        retail_rules=RetailAllocationRules(
            promoter_renunciation_percentage=0.0
        )
    ),
    "EFCIL": RightsIssue(
        details=RightsIssueDetails(
            symbol="EFCIL",
            company_name="EFC (I) Limited",
            base_issue_size_crores=150.0,
            old_shares_ratio=103,
            new_shares_ratio=8,
            issue_price=150.0,
            current_market_price=480.0
        ),
        timeline=RightsIssueTimeline(
            announcement_date=date(2026, 4, 15),
            record_date=date(2026, 5, 7),
            open_date=date(2026, 5, 13),
            renunciation_date=date(2026, 5, 18),
            close_date=date(2026, 5, 22),
            allotment_date=date(2026, 6, 5),
            listing_date=date(2026, 6, 15)
        ),
        payment_schedule=PaymentSchedule(
            is_partly_paid=False,
            ticker_symbol="EFCIL-RE",
            installments=[]
        ),
        retail_rules=RetailAllocationRules(
            promoter_renunciation_percentage=0.0
        )
    )
}

@router.get("/active", response_model=List[str])
async def get_active_issues():
    """Fetch active rights issues in allowed indices."""
    return list(MOCK_RIGHTS_ISSUES.keys())

@router.get("/{symbol}/chart")
async def get_rights_chart(symbol: str):
    """
    Fetches historical price data and adds Agentic Forecasts for future dates.
    """
    import yfinance as yf
    symbol = symbol.upper()
    if symbol not in MOCK_RIGHTS_ISSUES:
         raise HTTPException(status_code=404, detail="Rights issue not found")

    issue = MOCK_RIGHTS_ISSUES[symbol]
    start = issue.timeline.announcement_date

    # Use 'today' for the end of historical data
    today = date.today()
    hist_end = min(today, issue.timeline.listing_date)

    stock_ticker = f"{symbol}.NS"
    data = yf.download(stock_ticker, start=start, end=hist_end, progress=False)

    chart_data = []
    last_price = 0
    last_volume = 0

    # Track all milestone dates to ensure they are present in the data for Recharts matching
    milestone_dates = {
        issue.timeline.announcement_date,
        issue.timeline.record_date,
        issue.timeline.open_date,
        issue.timeline.renunciation_date,
        issue.timeline.close_date,
        issue.timeline.listing_date
    }

    for dt, row in data.iterrows():
        d_str = dt.strftime("%Y-%m-%d")
        last_price = round(float(row['Close']), 2)
        last_volume = int(row['Volume'])
        chart_data.append({
            "date": d_str,
            "price": last_price,
            "volume": last_volume,
            "type": "HISTORICAL"
        })

    # --- Agentic Forecast Engine ---
    if hist_end < issue.timeline.listing_date:
        curr_date = hist_end
        target_date = issue.timeline.listing_date

        # Simple Brownian Motion with drift for Rights Issues
        drift = -0.001
        volatility = 0.02

        while curr_date < target_date: # Stop exactly at target_date
            curr_date += timedelta(days=1)

            # Skip weekends UNLESS it's a milestone date (needed for ReferenceLine matching)
            is_milestone = curr_date in milestone_dates
            if curr_date.weekday() >= 5 and not is_milestone:
                continue

            change = 1 + drift + (random.uniform(-1, 1) * volatility)
            last_price = round(last_price * change, 2)
            last_volume = int(last_volume * (0.8 + random.random() * 0.4))

            chart_data.append({
                "date": curr_date.strftime("%Y-%m-%d"),
                "price": last_price,
                "volume": last_volume,
                "type": "FORECAST"
            })

    # Ensure chronologically sorted and deduplicated for Recharts to anchor ReferenceLines correctly
    chart_data.sort(key=lambda x: x['date'])
    seen_dates = set()
    final_chart = []
    for point in chart_data:
        if point['date'] not in seen_dates:
            final_chart.append(point)
            seen_dates.add(point['date'])
    chart_data = final_chart

    # Calculate RE Intrinsic Value chart
    re_start = issue.timeline.open_date
    re_end = issue.timeline.close_date
    re_data = []

    # RE data typically starts from open_date
    # If open_date is in future, we forecast RE as well
    if re_start > today:
        # Forecast RE Intrinsic Value
        # Use forecast data or last known price
        forecast_prices = [d['price'] for d in chart_data if d['date'] >= re_start.strftime("%Y-%m-%d")]
        if not forecast_prices:
            forecast_prices = [last_price] * 10 # Placeholder

        curr_re_date = re_start
        for p in forecast_prices:
            if curr_re_date > re_end: break
            intrinsic = max(0.0, p - issue.details.issue_price)
            re_data.append({
                "date": curr_re_date.strftime("%Y-%m-%d"),
                "price": round(intrinsic * 1.05, 2),
                "volume": int(last_volume * 0.1),
                "type": "RE_FORECAST"
            })
            curr_re_date += timedelta(days=1)
    else:
        # Mix of historical and forecast RE
        # For simplicity, we just use the existing re_window logic but ensure it handles forecast data
        re_window_data = [d for d in chart_data if d['date'] >= re_start.strftime("%Y-%m-%d") and d['date'] <= re_end.strftime("%Y-%m-%d")]
        for d in re_window_data:
            intrinsic = max(0.0, d['price'] - issue.details.issue_price)
            re_data.append({
                "date": d['date'],
                "price": round(intrinsic * 1.05, 2),
                "volume": int(d['volume'] * 0.1),
                "type": "RE"
            })

    return {
        "stock_chart": chart_data,
        "re_chart": re_data,
        "is_forecast": True if hist_end < issue.timeline.listing_date else False
    }

@router.get("/{symbol}", response_model=RightsIssue)
async def get_issue_details(symbol: str):
    """Fetch details and timeline for a specific rights issue."""
    logger.info(f"Fetching rights issue details for: {symbol}")
    symbol = symbol.upper()
    if symbol not in MOCK_RIGHTS_ISSUES:
        logger.warning(f"Rights issue not found in mock data: {symbol}")
        raise HTTPException(status_code=404, detail="Rights issue not found")
    return MOCK_RIGHTS_ISSUES[symbol]

class CalculateRequest(BaseModel):
    symbol: str
    current_holdings: int
    additional_shares_to_apply: int = 0

@router.post("/calculate")
async def calculate_scenario(req: CalculateRequest):
    """Calculates capital required, TERP, and scenarios for a user's holdings."""
    symbol = req.symbol.upper()
    if symbol not in MOCK_RIGHTS_ISSUES:
        raise HTTPException(status_code=404, detail="Rights issue not found")

    issue = MOCK_RIGHTS_ISSUES[symbol]

    pl_data = calculate_subscription_pl(
        holdings=req.current_holdings,
        market_price=issue.details.current_market_price,
        rights_price=issue.details.issue_price,
        old_ratio=issue.details.old_shares_ratio,
        new_ratio=issue.details.new_shares_ratio,
        additional_shares=req.additional_shares_to_apply
    )

    re_value = calculate_re_intrinsic_value(
        current_price=issue.details.current_market_price,
        rights_price=issue.details.issue_price
    )

    probability = calculate_additional_allotment_probability(
        is_undersubscribed=False,
        promoter_renunciation_pct=issue.retail_rules.promoter_renunciation_percentage
    )

    return {
        "pl_data": pl_data,
        "re_intrinsic_value": re_value,
        "additional_allotment_probability": probability,
        "tax_warning": "Selling REs is subject to Short-Term Capital Gains tax with a cost basis of zero."
    }

class AuditRequest(BaseModel):
    symbol: str
    filing_text: str

@router.post("/audit")
async def audit_rights_issue(req: AuditRequest):
    """Triggers the AI Agent Crew to analyze a rights issue filing."""
    try:
        result = run_ownerise_audit(req.filing_text)
        return {"symbol": req.symbol, "analysis": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
