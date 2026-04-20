"""
Heatmap route — monthly returns matrix for a given ticker.
GET /api/heatmap/{ticker}  →  last 3 years of monthly returns (% change)

Used by the Market Heatmap tab in the frontend.
"""
import yfinance as yf
import pandas as pd
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from src.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


@router.get("/{ticker}")
async def get_heatmap(ticker: str):
    """
    Downloads 3 years of daily OHLCV data from yfinance and computes
    the month-end to month-end percentage return for each month/year cell.

    Response shape:
    {
      "ticker": "TCS.NS",
      "years":  [2024, 2025, 2026],
      "months": ["Jan", ..., "Dec"],
      "data": { "2024": {"Jan": 3.4, "Feb": -1.2, ...}, ... },
      "best":  {"month": "Jan 2024", "return": 12.4},
      "worst": {"month": "Sep 2023", "return": -8.1}
    }
    """
    # Normalise ticker
    ticker_clean = ticker.strip().upper()
    if not ticker_clean.endswith(".NS") and not ticker_clean.endswith(".BO"):
        ticker_clean += ".NS"

    try:
        raw = yf.download(ticker_clean, period="3y", interval="1mo",
                          auto_adjust=True, progress=False)

        if raw.empty:
            return JSONResponse(status_code=404, content={"error": f"No data found for {ticker_clean}"})

        # Monthly close prices
        close = raw["Close"].squeeze()
        monthly_returns = close.pct_change() * 100   # % change

        # Build year → month → return dict
        data: dict[str, dict[str, float | None]] = {}
        years_seen: list[int] = []
        best = {"month": "", "return": float("-inf")}
        worst = {"month": "", "return": float("inf")}

        for idx, val in monthly_returns.items():
            # idx can be Timestamp or (Timestamp, ...) for MultiIndex
            ts = idx[0] if isinstance(idx, tuple) else idx
            year  = str(ts.year)
            month = MONTH_LABELS[ts.month - 1]

            if year not in data:
                data[year] = {}
                years_seen.append(int(year))

            rounded = round(float(val), 2) if not pd.isna(val) else None
            data[year][month] = rounded

            if rounded is not None:
                label = f"{month} {year}"
                if rounded > best["return"]:
                    best = {"month": label, "return": rounded}
                if rounded < worst["return"]:
                    worst = {"month": label, "return": rounded}

        years_seen = sorted(set(years_seen))

        return {
            "ticker":  ticker_clean,
            "years":   years_seen,
            "months":  MONTH_LABELS,
            "data":    data,
            "best":    best,
            "worst":   worst,
        }

    except Exception as e:
        logger.error(f"Heatmap failed for {ticker_clean}: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})
