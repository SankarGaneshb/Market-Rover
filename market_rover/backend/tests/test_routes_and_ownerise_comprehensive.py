"""
test_routes_and_ownerise_comprehensive.py — Exhaustive Unit Tests for Market Rover Routes and OwneRise Backend.
Covers:
  - src/routes/analysis.py
  - src/routes/analyze.py
  - src/routes/calendar.py
  - src/routes/heatmap.py
  - src/routes/shadow.py
  - src/routes/snapshot.py
  - ownerise/backend/calculations.py
  - ownerise/backend/router.py
  - ownerise/backend/orchestrator.py
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.routes import router as api_router
from src.routes import analysis
from src.utils.db_manager import db
from ownerise.backend.calculations import (
    calculate_terp,
    calculate_re_intrinsic_value,
    calculate_fractional_entitlement,
    calculate_subscription_pl,
    calculate_additional_allotment_probability,
)
from ownerise.backend.orchestrator import run_ownerise_audit

app = FastAPI()
app.include_router(api_router, prefix="/api")
client = TestClient(app)


# ── Helper for DataFrame with DatetimeIndex ───────────────────────────────────

def _make_ohlcv_df(rows=10, start="2024-01-01", freq="D"):
    dates = pd.date_range(start, periods=rows, freq=freq)
    return pd.DataFrame({
        "Open": np.linspace(100, 110, rows),
        "High": np.linspace(105, 115, rows),
        "Low": np.linspace(95, 105, rows),
        "Close": np.linspace(100, 110, rows),
        "Volume": [10000] * rows
    }, index=dates)


# ── 1. Analysis Routes Tests (src/routes/analysis.py) ───────────────────────────

def test_analysis_seasonality_success():
    sample_df = pd.DataFrame({
        "Month_Name": ["Jan", "Feb"],
        "Avg_Return": [2.5, -1.2],
        "Win_Rate": [65.0, 45.0],
        "Count": [10, 10]
    }, index=[1, 2])

    with patch("yfinance.download", return_value=_make_ohlcv_df(10)), \
         patch.object(analysis.analyzer, "calculate_seasonality", return_value=sample_df):
        res = client.get("/api/analysis/seasonality/TCS")
        assert res.status_code == 200
        data = res.json()
        assert data["ticker"] == "TCS.NS"
        assert len(data["data"]) == 2
        assert data["data"][0]["month_name"] == "Jan"


def test_analysis_seasonality_empty_404():
    with patch("yfinance.download", return_value=pd.DataFrame()):
        res = client.get("/api/analysis/seasonality/EMPTY")
        assert res.status_code == 404
        assert "error" in res.json()


def test_analysis_seasonality_exception_500():
    with patch("yfinance.download", side_effect=Exception("API limit")):
        res = client.get("/api/analysis/seasonality/ERR")
        assert res.status_code == 500
        assert "error" in res.json()


def test_analysis_forecast_sd_and_median():
    mock_raw = _make_ohlcv_df(10)
    # Test SD winner
    with patch("yfinance.download", return_value=mock_raw), \
         patch.object(analysis.analyzer, "backtest_strategies", return_value={"winner": "sd", "confidence": "HIGH"}), \
         patch.object(analysis.analyzer, "calculate_sd_strategy_forecast", return_value={
             "forecast_price": 150.0,
             "annualized_growth": 12.5,
             "projection_path": [{"date": datetime(2026, 12, 31), "price": 150.0}]
         }):
        res = client.get("/api/analysis/forecast/INFY")
        assert res.status_code == 200
        data = res.json()
        assert data["strategy"] == "sd"
        assert data["forecast_price"] == 150.0

    # Test Median winner
    with patch("yfinance.download", return_value=mock_raw), \
         patch.object(analysis.analyzer, "backtest_strategies", return_value={"winner": "median", "confidence": "MED"}), \
         patch.object(analysis.analyzer, "calculate_median_strategy_forecast", return_value={
             "forecast_price": 140.0,
             "annualized_growth": 8.5,
             "projection_path": [{"date": datetime(2026, 12, 31), "price": 140.0}]
         }):
        res = client.get("/api/analysis/forecast/INFY.BO")
        assert res.status_code == 200
        assert res.json()["strategy"] == "median"


def test_analysis_forecast_empty_and_exception():
    with patch("yfinance.download", return_value=pd.DataFrame()):
        res = client.get("/api/analysis/forecast/EMPTY")
        assert res.status_code == 404

    with patch("yfinance.download", side_effect=Exception("Timeout")):
        res = client.get("/api/analysis/forecast/ERR")
        assert res.status_code == 500


def test_analysis_backtest_success_and_errors():
    mock_raw = _make_ohlcv_df(10)
    backtest_data = {
        "winner": "sd",
        "median_avg_error": 5.2,
        "sd_avg_error": 3.1,
        "confidence": "HIGH",
        "years_tested": 5
    }
    with patch("yfinance.download", return_value=mock_raw), \
         patch.object(analysis.analyzer, "backtest_strategies", return_value=backtest_data):
        res = client.get("/api/analysis/backtest/RELIANCE")
        assert res.status_code == 200
        assert res.json()["winner"] == "sd"
        assert res.json()["sd_avg_error"] == 3.1

    with patch("yfinance.download", return_value=pd.DataFrame()):
        res = client.get("/api/analysis/backtest/EMPTY")
        assert res.status_code == 404

    with patch("yfinance.download", side_effect=Exception("DB fail")):
        res = client.get("/api/analysis/backtest/ERR")
        assert res.status_code == 500


def test_analysis_heatmap_success_and_errors():
    mock_raw = _make_ohlcv_df(10)
    matrix_df = pd.DataFrame({
        "Jan": [2.5, 3.0],
        "Feb": [None, -1.0]
    }, index=[2025, 2026])

    with patch("yfinance.download", return_value=mock_raw), \
         patch.object(analysis.analyzer, "calculate_monthly_returns_matrix", return_value=matrix_df):
        res = client.get("/api/analysis/heatmap/SBIN")
        assert res.status_code == 200
        data = res.json()
        assert "2026" in data["data"]
        assert data["years"] == [2026, 2025]

    with patch("yfinance.download", return_value=pd.DataFrame()):
        res = client.get("/api/analysis/heatmap/EMPTY")
        assert res.status_code == 404

    with patch("yfinance.download", side_effect=Exception("Calc error")):
        res = client.get("/api/analysis/heatmap/ERR")
        assert res.status_code == 500


# ── 2. Snapshot Route Tests (src/routes/snapshot.py) ────────────────────────────

def test_snapshot_fast_info_success():
    dates = pd.date_range("2024-01-01", periods=260, freq="D")
    hist_df = pd.DataFrame({
        "Close": np.linspace(100, 200, 260)
    }, index=dates)

    mock_ticker = MagicMock()
    mock_ticker.fast_info = {
        "lastPrice": 200.0,
        "previousClose": 195.0,
        "open": 196.0,
        "dayHigh": 202.0,
        "dayLow": 194.0,
        "yearHigh": 210.0,
        "yearLow": 90.0,
    }
    mock_ticker.history.return_value = hist_df

    with patch("market_rover.backend.src.routes.snapshot.yf.Ticker", return_value=mock_ticker):
        res = client.get("/api/snapshot/TCS.NS")
        assert res.status_code == 200
        data = res.json()
        assert data["ticker"] == "TCS.NS"
        assert data["metrics"]["current_price"] == 200.0
        assert data["metrics"]["upper_circuit"] > 0
        assert len(data["chart_data"]) > 0


def test_snapshot_fallback_to_info_and_empty_hist():
    mock_ticker = MagicMock()
    type(mock_ticker).fast_info = property(lambda self: (_ for _ in ()).throw(Exception("No fast_info")))
    mock_ticker.info = {
        "currentPrice": 150.0,
        "previousClose": 148.0,
        "open": 149.0,
        "dayHigh": 152.0,
        "dayLow": 147.0,
        "fiftyTwoWeekHigh": 160.0,
        "fiftyTwoWeekLow": 100.0
    }
    mock_ticker.history.return_value = pd.DataFrame()

    with patch("market_rover.backend.src.routes.snapshot.yf.Ticker", return_value=mock_ticker):
        res = client.get("/api/snapshot/INFY.NS")
        assert res.status_code == 200
        data = res.json()
        assert data["metrics"]["current_price"] == 150.0
        assert data["chart_data"] == []


def test_snapshot_exception_500():
    with patch("market_rover.backend.src.routes.snapshot.yf.Ticker", side_effect=Exception("Fatal Ticker Error")):
        res = client.get("/api/snapshot/ERROR.NS")
        assert res.status_code == 500
        assert "error" in res.json()


# ── 3. Shadow Route Tests (src/routes/shadow.py) ───────────────────────────────

def test_shadow_market_success_and_exception():
    mock_rows = [
        {
            "ticker": "TCS.NS",
            "stance": "ACCUMULATION",
            "logic_summary": "Institutional buying detected",
            "analysis_date": datetime(2026, 9, 20, 10, 0),
            "user_id": "u1"
        }
    ]
    mock_pool = MagicMock()
    mock_conn = AsyncMock()
    mock_conn.fetch.return_value = mock_rows
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    mock_pool.acquire.return_value.__aexit__ = AsyncMock()

    with patch.object(db, "connect", AsyncMock()), patch.object(db, "pool", mock_pool):
        res = client.get("/api/shadow/market")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["ticker"] == "TCS.NS"
        assert "2026-09-20" in data[0]["analysis_date"]

    with patch.object(db, "connect", side_effect=Exception("DB Down")):
        res = client.get("/api/shadow/market")
        assert res.status_code == 500


def test_shadow_user_query_and_path_params():
    mock_rows = [
        {
            "ticker": "INFY.NS",
            "stance": "DISTRIBUTION",
            "logic_summary": "Heavy block sale",
            "analysis_date": datetime(2026, 9, 21, 12, 0)
        }
    ]
    mock_pool = MagicMock()
    mock_conn = AsyncMock()
    mock_conn.fetch.return_value = mock_rows
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    mock_pool.acquire.return_value.__aexit__ = AsyncMock()

    with patch.object(db, "connect", AsyncMock()), patch.object(db, "pool", mock_pool):
        # Query parameter with handle
        res = client.get("/api/shadow?user_handle=test_user")
        assert res.status_code == 200
        assert len(res.json()["shadow_signals"]) == 1

        # Query parameter without handle (market signals)
        res2 = client.get("/api/shadow")
        assert res2.status_code == 200
        assert len(res2.json()["shadow_signals"]) == 1

        # Path parameter
        res3 = client.get("/api/shadow/test_user")
        assert res3.status_code == 200
        assert len(res3.json()["shadow_signals"]) == 1

    with patch.object(db, "connect", side_effect=Exception("Connection pool dead")):
        res = client.get("/api/shadow?user_handle=test_user")
        assert res.status_code == 500


# ── 4. Calendar Route Tests (src/routes/calendar.py) ───────────────────────────

def test_calendar_muhurtham_and_seasonal():
    res = client.get("/api/calendar/muhurtham/2026")
    assert res.status_code == 200
    data = res.json()
    assert data["year"] == 2026
    assert data["count"] > 0

    res_unknown = client.get("/api/calendar/muhurtham/2099")
    assert res_unknown.status_code == 200
    assert "windows" in res_unknown.json()

    res_seasonal = client.get("/api/calendar/seasonal")
    assert res_seasonal.status_code == 200
    assert len(res_seasonal.json()["patterns"]) >= 5


def test_calendar_unified():
    res = client.get("/api/calendar")
    assert res.status_code == 200
    events = res.json()["calendar"]
    assert any(e["type"] == "Buy" for e in events)
    assert any(e["type"] == "Accumulate" for e in events)


# ── 5. Heatmap Route Tests (src/routes/heatmap.py) ─────────────────────────────

def test_heatmap_route_success_and_errors():
    dates = pd.date_range("2024-01-01", periods=12, freq="MS")
    close_series = pd.Series([100.0, 105.0, 102.0, 110.0, 115.0, 120.0, 118.0, 125.0, 130.0, 128.0, 135.0, 140.0], index=dates)
    mock_raw = pd.DataFrame({"Close": close_series})

    with patch("yfinance.download", return_value=mock_raw):
        res = client.get("/api/heatmap/RELIANCE.NS")
        assert res.status_code == 200
        data = res.json()
        assert data["ticker"] == "RELIANCE.NS"
        assert "2024" in data["data"]
        assert data["best"]["month"] != ""

    with patch("yfinance.download", return_value=pd.DataFrame()):
        res = client.get("/api/heatmap/EMPTY.NS")
        assert res.status_code == 404

    with patch("yfinance.download", side_effect=Exception("YF Blocked")):
        res = client.get("/api/heatmap/ERR.NS")
        assert res.status_code == 500


# ── 6. Analyze Route Tests (src/routes/analyze.py) ─────────────────────────────

@pytest.mark.asyncio
async def test_analyze_route_workflow():
    from market_rover.backend.src.routes import analyze

    with patch.object(analyze._graph, "ainvoke", new_callable=AsyncMock) as mock_invoke, \
         patch.object(analyze.db, "connect", AsyncMock()), \
         patch.object(analyze.db, "store_memory", AsyncMock()):
        mock_invoke.return_value = {"status": "DONE", "tickers": ["TCS.NS"]}

        res = client.post("/api/analyze", json={"tickers": ["TCS.NS"], "discoverable_handle": "test_user"})
        assert res.status_code == 200
        task_id = res.json()["task_id"]

        # Poll status
        status_res = client.get(f"/api/analyze/status/{task_id}")
        assert status_res.status_code == 200
        assert status_res.json()["status"] in ["pending", "completed"]

        # Not found task
        not_found_res = client.get("/api/analyze/status/task_nonexistent_9999")
        assert not_found_res.status_code == 404


# ── 7. OwneRise Calculations Tests (ownerise/backend/calculations.py) ──────────

def test_ownerise_calculations_complete():
    # 1. calculate_terp
    terp = calculate_terp(pre_issue_price=100.0, rights_price=80.0, old_ratio=4, new_ratio=1)
    assert terp == 96.0

    # 2. calculate_re_intrinsic_value
    re_val = calculate_re_intrinsic_value(current_price=120.0, rights_price=100.0)
    assert re_val == 20.0
    re_val_zero = calculate_re_intrinsic_value(current_price=80.0, rights_price=100.0)
    assert re_val_zero == 0.0

    # 3. calculate_fractional_entitlement
    frac = calculate_fractional_entitlement(holdings=105, old_ratio=10, new_ratio=1)
    assert frac["whole_shares"] == 10
    assert frac["fractional_shares"] == 0.5
    assert len(frac["fraction_warning"]) > 0

    no_frac = calculate_fractional_entitlement(holdings=100, old_ratio=10, new_ratio=1)
    assert no_frac["fractional_shares"] == 0.0
    assert no_frac["fraction_warning"] == ""

    # 4. calculate_subscription_pl
    pl = calculate_subscription_pl(
        holdings=100,
        market_price=150.0,
        rights_price=100.0,
        old_ratio=10,
        new_ratio=1,
        additional_shares=5
    )
    assert pl["entitled_shares"] == 10
    assert pl["total_shares_applied"] == 15
    assert pl["capital_required"] == 1500.0
    assert pl["new_total_holdings"] == 115
    assert pl["new_average_cost"] > 0
    assert pl["projected_terp"] > 0

    # Test edge zero holdings
    pl_zero = calculate_subscription_pl(
        holdings=0,
        market_price=100.0,
        rights_price=80.0,
        old_ratio=1,
        new_ratio=1,
        additional_shares=0
    )
    assert pl_zero["new_total_holdings"] == 0
    assert pl_zero["new_average_cost"] == 0

    # 5. calculate_additional_allotment_probability
    assert "HIGH" in calculate_additional_allotment_probability(is_undersubscribed=True, promoter_renunciation_pct=0.0)
    assert "HIGH" in calculate_additional_allotment_probability(is_undersubscribed=False, promoter_renunciation_pct=60.0)
    assert "MEDIUM" in calculate_additional_allotment_probability(is_undersubscribed=False, promoter_renunciation_pct=25.0)
    assert "LOW" in calculate_additional_allotment_probability(is_undersubscribed=False, promoter_renunciation_pct=5.0)


# ── 8. OwneRise Router Tests (ownerise/backend/router.py) ───────────────────────

def test_ownerise_router_endpoints():
    # 1. Active issues
    res_act = client.get("/api/v1/ownerise/active")
    assert res_act.status_code == 200
    assert "RELIANCE" in res_act.json()

    # 2. Issue details
    res_det = client.get("/api/v1/ownerise/RELIANCE")
    assert res_det.status_code == 200
    assert res_det.json()["details"]["symbol"] == "RELIANCE"

    res_det_404 = client.get("/api/v1/ownerise/UNKNOWN")
    assert res_det_404.status_code == 404

    # 3. Calculate scenario
    calc_payload = {
        "symbol": "RELIANCE",
        "current_holdings": 150,
        "additional_shares_to_apply": 5
    }
    res_calc = client.post("/api/v1/ownerise/calculate", json=calc_payload)
    assert res_calc.status_code == 200
    data = res_calc.json()
    assert "pl_data" in data
    assert "re_intrinsic_value" in data
    assert "additional_allotment_probability" in data

    res_calc_404 = client.post("/api/v1/ownerise/calculate", json={"symbol": "UNKNOWN", "current_holdings": 10})
    assert res_calc_404.status_code == 404

    # 4. Chart endpoint (mock yfinance)
    dates = pd.date_range("2020-04-30", periods=20, freq="D")
    df_chart = pd.DataFrame({
        "Close": np.linspace(1200, 1400, 20),
        "Volume": [100000] * 20
    }, index=dates)

    with patch("yfinance.download", return_value=df_chart):
        res_chart = client.get("/api/v1/ownerise/RELIANCE/chart")
        assert res_chart.status_code == 200
        chart_data = res_chart.json()
        assert "stock_chart" in chart_data
        assert "re_chart" in chart_data

    # Chart 404
    res_chart_404 = client.get("/api/v1/ownerise/UNKNOWN/chart")
    assert res_chart_404.status_code == 404


def test_ownerise_audit_and_orchestrator():
    # 1. Audit endpoint success
    with patch("ownerise.backend.router.run_ownerise_audit", return_value="Audit completed successfully"):
        res_aud = client.post("/api/v1/ownerise/audit", json={
            "symbol": "RELIANCE",
            "filing_text": "Sample Rights Issue Letter of Offer"
        })
        assert res_aud.status_code == 200
        assert res_aud.json()["analysis"] == "Audit completed successfully"

    # 2. Audit endpoint error
    with patch("ownerise.backend.router.run_ownerise_audit", side_effect=Exception("Crew execution failed")):
        res_err = client.post("/api/v1/ownerise/audit", json={
            "symbol": "RELIANCE",
            "filing_text": "Sample Rights Issue Letter of Offer"
        })
        assert res_err.status_code == 500

    # 3. Direct Orchestrator unit test with Crew mock
    with patch("ownerise.backend.orchestrator.Crew") as mock_crew:
        mock_instance = MagicMock()
        mock_instance.kickoff.return_value = "Mocked Crew Result"
        mock_crew.return_value = mock_instance

        res = run_ownerise_audit("Test Filing")
        assert res == "Mocked Crew Result"
        mock_instance.kickoff.assert_called_once()
