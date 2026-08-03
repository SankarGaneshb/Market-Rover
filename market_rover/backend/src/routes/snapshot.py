import os
import yfinance as yf
import pandas as pd
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from src.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

class SnapshotResponse(BaseModel):
    ticker: str
    metrics: dict
    chart_data: list

@router.get("/{ticker}", response_model=SnapshotResponse)
async def get_snapshot(ticker: str):
    """
    Fetches real-time stock snapshot data and 1-year history with 50/200 DMA.
    """
    logger.info(f"Fetching snapshot data for {ticker}")
    try:
        stock = yf.Ticker(ticker)

        # 1. Fetch Fast Info / Info for real-time metrics
        try:
            info = stock.fast_info
            current_price = info.get("lastPrice") or info.get("previousClose")
            prev_close = info.get("previousClose")
            open_price = info.get("open")
            day_high = info.get("dayHigh")
            day_low = info.get("dayLow")
            fifty_two_high = info.get("yearHigh")
            fifty_two_low = info.get("yearLow")
        except Exception as e:
            logger.warning(f"fast_info failed for {ticker}, falling back to info: {e}")
            info = stock.info
            current_price = info.get("currentPrice") or info.get("previousClose")
            prev_close = info.get("previousClose")
            open_price = info.get("open")
            day_high = info.get("dayHigh")
            day_low = info.get("dayLow")
            fifty_two_high = info.get("fiftyTwoWeekHigh")
            fifty_two_low = info.get("fiftyTwoWeekLow")

        # Fallbacks if fast_info/info is incomplete
        if not current_price: current_price = 0
        if not prev_close: prev_close = current_price

        # 2. Estimate Circuit Limits (Standard +/- 20% for NSE if not explicitly available)
        upper_circuit = prev_close * 1.20 if prev_close else 0
        lower_circuit = prev_close * 0.80 if prev_close else 0

        # 3. Fetch Historical Data (2 years to calculate 200 DMA accurately)
        hist = stock.history(period="2y")

        dma_50 = 0
        dma_200 = 0
        chart_data = []

        if not hist.empty:
            # Calculate Moving Averages
            hist['50_DMA'] = hist['Close'].rolling(window=50).mean()
            hist['200_DMA'] = hist['Close'].rolling(window=200).mean()

            # Get latest DMAs
            dma_50 = hist['50_DMA'].iloc[-1] if len(hist) >= 50 and pd.notna(hist['50_DMA'].iloc[-1]) else 0
            dma_200 = hist['200_DMA'].iloc[-1] if len(hist) >= 200 and pd.notna(hist['200_DMA'].iloc[-1]) else 0

            # Calculate MACD
            exp1 = hist['Close'].ewm(span=12, adjust=False).mean()
            exp2 = hist['Close'].ewm(span=26, adjust=False).mean()
            hist['MACD'] = exp1 - exp2
            hist['MACD_Signal'] = hist['MACD'].ewm(span=9, adjust=False).mean()

            # Calculate RSI (14-day)
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).fillna(0)
            loss = (-delta.where(delta < 0, 0)).fillna(0)
            avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
            avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
            rs = avg_gain / avg_loss
            hist['RSI'] = 100 - (100 / (1 + rs))

            # Truncate to the last 1 year (approx 252 trading days) for the chart
            hist_1y = hist.tail(252)

            for index, row in hist_1y.iterrows():
                chart_data.append({
                    "date": index.strftime('%Y-%m-%d'),
                    "close": round(row['Close'], 2) if pd.notna(row['Close']) else None,
                    "dma_50": round(row['50_DMA'], 2) if pd.notna(row['50_DMA']) else None,
                    "dma_200": round(row['200_DMA'], 2) if pd.notna(row['200_DMA']) else None,
                    "macd": round(row['MACD'], 2) if pd.notna(row['MACD']) else None,
                    "macd_signal": round(row['MACD_Signal'], 2) if pd.notna(row['MACD_Signal']) else None,
                    "rsi": round(row['RSI'], 2) if pd.notna(row['RSI']) else None
                })

        # 4. Calculate Distance Percentages
        dma_50_dist = ((current_price - dma_50) / dma_50 * 100) if dma_50 else 0
        dma_200_dist = ((current_price - dma_200) / dma_200 * 100) if dma_200 else 0

        # 5. Calculate Thermometer Positions (0 to 100)
        range_52w_pos = 0
        if fifty_two_high and fifty_two_low and (fifty_two_high > fifty_two_low):
             range_52w_pos = ((current_price - fifty_two_low) / (fifty_two_high - fifty_two_low)) * 100

        circuit_pos = 0
        if upper_circuit and lower_circuit and (upper_circuit > lower_circuit):
             circuit_pos = ((current_price - lower_circuit) / (upper_circuit - lower_circuit)) * 100

        metrics = {
            "current_price": round(current_price, 2) if current_price else None,
            "prev_close": round(prev_close, 2) if prev_close else None,
            "open": round(open_price, 2) if open_price else None,
            "day_high": round(day_high, 2) if day_high else None,
            "day_low": round(day_low, 2) if day_low else None,
            "52w_high": round(fifty_two_high, 2) if fifty_two_high else None,
            "52w_low": round(fifty_two_low, 2) if fifty_two_low else None,
            "dma_50": round(dma_50, 2) if dma_50 else None,
            "dma_200": round(dma_200, 2) if dma_200 else None,
            "upper_circuit": round(upper_circuit, 2),
            "lower_circuit": round(lower_circuit, 2),
            "dma_50_dist_pct": round(dma_50_dist, 2),
            "dma_200_dist_pct": round(dma_200_dist, 2),
            "range_52w_pos": max(0, min(100, round(range_52w_pos, 2))),
            "circuit_pos": max(0, min(100, round(circuit_pos, 2)))
        }

        return SnapshotResponse(ticker=ticker, metrics=metrics, chart_data=chart_data)

    except Exception as e:
        logger.error(f"Error fetching snapshot for {ticker}: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": "Failed to fetch snapshot data", "details": str(e)})
