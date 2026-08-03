from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
import yfinance as yf
import pandas as pd
from rover_tools.analytics import AnalyzersUnified as MarketAnalyzer
from src.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)
analyzer = MarketAnalyzer()

@router.get("/seasonality/{ticker}")
async def get_seasonality(ticker: str, exclude_outliers: bool = False):
    """
    Returns robust seasonality statistics (Avg Return, Win Rate per month).
    Matches legacy Streamlit 'Market Analysis' tab logic.
    """
    ticker_clean = ticker.strip().upper()
    if not ticker_clean.endswith(".NS") and not ticker_clean.endswith(".BO"):
        ticker_clean += ".NS"

    try:
        # Fetch max history for seasonality
        raw = yf.download(ticker_clean, period="max", auto_adjust=True, progress=False)
        if raw.empty:
            return JSONResponse(status_code=404, content={"error": f"No data for {ticker_clean}"})

        stats = analyzer.calculate_seasonality(raw, exclude_outliers=exclude_outliers)

        # Convert to JSON-friendly format
        result = []
        for month_idx, row in stats.iterrows():
            result.append({
                "month": int(month_idx),
                "month_name": row["Month_Name"],
                "avg_return": round(float(row["Avg_Return"]), 2),
                "win_rate": round(float(row["Win_Rate"]), 2),
                "count": int(row["Count"])
            })

        return {
            "ticker": ticker_clean,
            "exclude_outliers": exclude_outliers,
            "data": result
        }
    except Exception as e:
        logger.error(f"Seasonality failed for {ticker_clean}: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/forecast/{ticker}")
async def get_robust_forecast(ticker: str, exclude_outliers: bool = False, target_date: str = "2026-12-31"):
    """
    Returns robust multi-scenario price forecasts (Conservative, Baseline, Aggressive).
    Matches legacy Streamlit 'Forecast' and 'Market Analysis' logic.
    """
    ticker_clean = ticker.strip().upper()
    if not ticker_clean.endswith(".NS") and not ticker_clean.endswith(".BO"):
        ticker_clean += ".NS"

    try:
        raw = yf.download(ticker_clean, period="max", auto_adjust=True, progress=False)
        if raw.empty:
            return JSONResponse(status_code=404, content={"error": f"No data for {ticker_clean}"})

        # Run Backtest to pick winner
        backtest_res = analyzer.backtest_strategies(raw, exclude_outliers=exclude_outliers)
        winner = backtest_res["winner"]

        # Run Forecast for the winning strategy
        if winner == "sd":
            res = analyzer.calculate_sd_strategy_forecast(raw, target_date=target_date, exclude_outliers=exclude_outliers)
        else:
            res = analyzer.calculate_median_strategy_forecast(raw, target_date=target_date, exclude_outliers=exclude_outliers)

        return {
            "ticker": ticker_clean,
            "strategy": winner,
            "confidence": backtest_res["confidence"],
            "target_date": target_date,
            "current_price": round(float(raw["Close"].iloc[-1]), 2),
            "forecast_price": round(float(res["forecast_price"]), 2),
            "annualized_growth": round(float(res["annualized_growth"]), 2),
            "projection_path": [{"date": p["date"].isoformat(), "price": round(float(p["price"]), 2)} for p in res["projection_path"]]
        }
    except Exception as e:
        logger.error(f"Forecast failed for {ticker_clean}: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/backtest/{ticker}")
async def get_strategy_backtest(ticker: str, exclude_outliers: bool = False):
    """
    Backtests Median vs SD strategies to determine predictive accuracy.
    """
    ticker_clean = ticker.strip().upper()
    if not ticker_clean.endswith(".NS") and not ticker_clean.endswith(".BO"):
        ticker_clean += ".NS"

    try:
        raw = yf.download(ticker_clean, period="max", auto_adjust=True, progress=False)
        if raw.empty:
            return JSONResponse(status_code=404, content={"error": f"No data for {ticker_clean}"})

        res = analyzer.backtest_strategies(raw, exclude_outliers=exclude_outliers)
        return {
            "ticker": ticker_clean,
            "winner": res["winner"],
            "median_avg_error": round(float(res["median_avg_error"]), 2),
            "sd_avg_error": round(float(res["sd_avg_error"]), 2),
            "confidence": res["confidence"],
            "years_tested": res["years_tested"]
        }
    except Exception as e:
        logger.error(f"Backtest failed for {ticker_clean}: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/heatmap/{ticker}")
async def get_robust_heatmap(ticker: str, exclude_outliers: bool = False):
    """
    Returns Year x Month returns matrix using the robust engine.
    Matches legacy Streamlit 'Market Analysis' tab logic.
    """
    ticker_clean = ticker.strip().upper()
    if not ticker_clean.endswith(".NS") and not ticker_clean.endswith(".BO"):
        ticker_clean += ".NS"

    try:
        raw = yf.download(ticker_clean, period="5y", auto_adjust=True, progress=False)
        if raw.empty:
            return JSONResponse(status_code=404, content={"error": f"No data for {ticker_clean}"})

        matrix = analyzer.calculate_monthly_returns_matrix(raw, exclude_outliers=exclude_outliers)

        # Convert matrix to dict
        data = {}
        for year, row in matrix.iterrows():
            data[str(year)] = {m: (round(float(v), 2) if pd.notna(v) else None) for m, v in row.items()}

        return {
            "ticker": ticker_clean,
            "exclude_outliers": exclude_outliers,
            "years": sorted([int(y) for y in data.keys()], reverse=True),
            "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
            "data": data
        }
    except Exception as e:
        logger.error(f"Heatmap failed for {ticker_clean}: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
