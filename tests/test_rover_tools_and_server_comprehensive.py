"""
test_rover_tools_and_server_comprehensive.py — Comprehensive Unit Test Suite for rover_tools & server.py.
Covers:
  - rover_tools/analytics/win_rate.py
  - rover_tools/advanced_skills.py
  - rover_tools/portfolio_tool.py
  - rover_tools/global_market_tool.py
  - rover_tools/forensic_tool.py
  - rover_tools/corporate_actions_tool.py
  - rover_tools/search_tool.py
  - rover_tools/sre_tools.py
  - rover_tools/autonomy_tools.py
  - rover_tools/hil_client.py
  - rover_tools/hil_governance.py
  - rover_tools/memory_tool.py
  - rover_tools/generate_daily_report.py
  - rover_tools/batch_backtester.py
  - rover_tools/market_context_tool.py
  - rover_tools/vismera_client.py
  - rover_tools/stock_data_tool.py
  - rover_tools/news_scraper_tool.py
  - server.py (FastAPI endpoints, Vismera bridge, CrewAI analysis, SPA router)
"""
import pytest
import os
import sys
import json
import tempfile
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient

# ==============================================================================
# 1. ROVER_TOOLS / ANALYTICS / WIN_RATE.PY
# ==============================================================================
from rover_tools.analytics.win_rate import (
    calculate_seasonality_win_rate,
    get_performance_stars
)

def test_calculate_seasonality_win_rate_success():
    """Verify seasonality win rate calculation across simulated monthly returns."""
    dates = pd.date_range(start="2015-01-01", end="2024-12-31", freq="MS")
    df_prices = pd.DataFrame({
        "RELIANCE.NS": np.linspace(1000, 2500, len(dates)),
        "TCS.NS": np.linspace(2000, 3800, len(dates))
    }, index=dates)

    with patch("yfinance.download", return_value={"Close": df_prices}):
        with patch("rover_tools.analytics.win_rate.get_common_tickers", return_value=["RELIANCE.NS - Reliance", "TCS.NS - TCS"]):
            results = calculate_seasonality_win_rate(category="Nifty 50", target_month=1, period="10y", top_n=2)
            assert isinstance(results, list)
            assert len(results) <= 2
            if results:
                assert "ticker" in results[0]
                assert "win_rate" in results[0]
                assert "avg_return" in results[0]

def test_calculate_seasonality_win_rate_with_outlier_exclusion():
    """Verify IQR outlier exclusion when computing seasonality win rates."""
    dates = pd.date_range(start="2018-01-01", end="2024-12-31", freq="MS")
    prices = np.linspace(100, 200, len(dates))
    df_prices = pd.DataFrame({"INFY.NS": prices}, index=dates)

    with patch("yfinance.download", return_value={"Close": df_prices}):
        with patch("rover_tools.analytics.win_rate.get_common_tickers", return_value=["INFY.NS - Infosys"]):
            results = calculate_seasonality_win_rate(category="Nifty 50", target_month=3, exclude_outliers=True)
            assert isinstance(results, list)

def test_calculate_seasonality_win_rate_errors_and_empty():
    """Verify error handling when yfinance fails or data is empty."""
    with patch("yfinance.download", side_effect=Exception("Network Timeout")):
        with patch("rover_tools.analytics.win_rate.get_common_tickers", return_value=["INFY.NS - Infosys"]):
            results = calculate_seasonality_win_rate(category="Nifty 50", target_month=5)
            assert results == []

    with patch("yfinance.download", return_value={"Close": pd.DataFrame()}):
        with patch("rover_tools.analytics.win_rate.get_common_tickers", return_value=["INFY.NS - Infosys"]):
            results = calculate_seasonality_win_rate(category="Nifty 50")
            assert results == []

def test_get_performance_stars_success_and_periods():
    """Verify get_performance_stars across 1y, 3y, 5y, 5y+ periods."""
    dates = pd.date_range(start="2018-01-01", end="2024-01-01", freq="W")
    df_prices = pd.DataFrame({
        ("RELIANCE.NS", "Close"): np.linspace(1000, 2500, len(dates)),
        ("TCS.NS", "Close"): np.linspace(2000, 3500, len(dates))
    }, index=dates)
    df_prices.columns = pd.MultiIndex.from_tuples(df_prices.columns)

    with patch("yfinance.download", return_value=df_prices):
        with patch("rover_tools.analytics.win_rate.get_common_tickers", return_value=["RELIANCE.NS - Reliance", "TCS.NS - TCS"]):
            stars_1y = get_performance_stars(category="Nifty 50", period="1y", top_n=2)
            assert isinstance(stars_1y, list)

            stars_3y = get_performance_stars(category="Nifty 50", period="3y", top_n=2)
            assert isinstance(stars_3y, list)

            stars_5y = get_performance_stars(category="Nifty 50", period="5y", top_n=2)
            assert isinstance(stars_5y, list)

            stars_5yp = get_performance_stars(category="Nifty 50", period="5y+", top_n=2)
            assert isinstance(stars_5yp, list)

def test_get_performance_stars_flat_columns_and_errors():
    """Verify get_performance_stars with flat dataframe, empty tickers, or download exceptions."""
    with patch("rover_tools.analytics.win_rate.get_common_tickers", return_value=[]):
        assert get_performance_stars() == []

    with patch("yfinance.download", side_effect=Exception("API limit")):
        with patch("rover_tools.analytics.win_rate.get_common_tickers", return_value=["RELIANCE.NS - Reliance"]):
            assert get_performance_stars() == []

    dates = pd.date_range(start="2020-01-01", end="2024-01-01", freq="W")
    flat_df = pd.DataFrame({"Close": np.linspace(100, 200, len(dates))}, index=dates)
    with patch("yfinance.download", return_value=flat_df):
        with patch("rover_tools.analytics.win_rate.get_common_tickers", return_value=["RELIANCE.NS - Reliance"]):
            stars = get_performance_stars(category="Nifty 50", period="1y")
            assert isinstance(stars, list)


# ==============================================================================
# 2. ROVER_TOOLS / ADVANCED_SKILLS.PY
# ==============================================================================
from rover_tools.advanced_skills import (
    calculate_portfolio_risk_tool,
    fetch_economic_calendar_tool,
    analyze_retail_sentiment_tool,
    detect_technical_patterns_tool,
    fetch_fii_dii_flow_tool,
    fetch_subha_muhurtham_tool,
    analyze_traditional_calendar_tool,
    fetch_historical_context_tool,
    generate_sector_heatmap_tool,
    fetch_options_skew_tool,
    calculate_mtc_score_tool,
    detect_institutional_absorption_tool
)

def test_advanced_skills_tools_execution():
    """Verify execution of all CrewAI advanced skills tools."""
    res_risk = calculate_portfolio_risk_tool.run(portfolio_json=json.dumps([{"ticker": "INFY.NS", "sector": "IT", "weight": 0.5}]))
    assert "Portfolio Risk" in res_risk

    res_cal = fetch_economic_calendar_tool.run(start_date="2026-03-01", end_date="2026-03-07")
    assert "Economic Calendar" in res_cal

    res_sent = analyze_retail_sentiment_tool.run(ticker="RELIANCE.NS")
    assert "Retail Sentiment" in res_sent

    res_flow = fetch_fii_dii_flow_tool.run(date="2026-03-01")
    assert "Institutional Flow" in res_flow

    res_muh = fetch_subha_muhurtham_tool.run(year=2026)
    assert "Muhurtham Data 2026" in res_muh

    res_trad_jewel = analyze_traditional_calendar_tool.run(sector="Jewelry")
    assert "wedding season" in res_trad_jewel
    res_trad_norm = analyze_traditional_calendar_tool.run(sector="IT")
    assert "Normal seasonal flows" in res_trad_norm

    res_hist = fetch_historical_context_tool.run(topic="Nifty Trend")
    assert "Historical Context" in res_hist

    res_heat = generate_sector_heatmap_tool.run()
    assert "Sector Heatmap successfully generated" in res_heat

    res_skew = fetch_options_skew_tool.run(ticker="RELIANCE.NS")
    assert "Options Skew" in res_skew

    res_abs = detect_institutional_absorption_tool.run(ticker="HDFCBANK.NS")
    assert "Absorption Detection" in res_abs

def test_detect_technical_patterns_tool():
    """Verify technical pattern detector under bullish, bearish, and empty conditions."""
    dates = pd.date_range(start="2024-01-01", periods=40, freq="D")
    df = pd.DataFrame({"Close": np.linspace(100, 150, 40)}, index=dates)

    with patch("yfinance.download", return_value=df):
        res = detect_technical_patterns_tool.run(ticker="INFY.NS")
        assert "Pattern Detection for INFY.NS" in res
        assert "RSI" in res

    with patch("yfinance.download", return_value=pd.DataFrame()):
        res = detect_technical_patterns_tool.run(ticker="UNKNOWN.NS")
        assert "No technical data" in res

    with patch("yfinance.download", side_effect=Exception("Failed")):
        res = detect_technical_patterns_tool.run(ticker="ERR.NS")
        assert "Failed to detect technical patterns" in res

def test_calculate_mtc_score_tool():
    """Verify multi-timeframe concordance tool with bullish and bearish trends."""
    d_dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
    h_dates = pd.date_range(start="2024-01-25", periods=30, freq="h")

    d_bull = pd.DataFrame({"Close": np.linspace(100, 200, 30)}, index=d_dates)
    h_bull = pd.DataFrame({"Close": np.linspace(150, 200, 30)}, index=h_dates)

    with patch("yfinance.download", side_effect=[d_bull, h_bull]):
        res_bull = calculate_mtc_score_tool.run(ticker="TCS.NS")
        assert "STRONG BUY CONCORDANCE" in res_bull

    d_bear = pd.DataFrame({"Close": np.linspace(200, 100, 30)}, index=d_dates)
    h_bear = pd.DataFrame({"Close": np.linspace(150, 100, 30)}, index=h_dates)

    with patch("yfinance.download", side_effect=[d_bear, h_bear]):
        res_bear = calculate_mtc_score_tool.run(ticker="TCS.NS")
        assert "STRONG SELL CONCORDANCE" in res_bear

    with patch("yfinance.download", side_effect=[pd.DataFrame(), pd.DataFrame()]):
        res_empty = calculate_mtc_score_tool.run(ticker="TCS.NS")
        assert "Insufficient Data" in res_empty


# ==============================================================================
# 3. ROVER_TOOLS / PORTFOLIO_TOOL.PY
# ==============================================================================
from rover_tools.portfolio_tool import read_portfolio

def test_read_portfolio_valid_and_errors(tmp_path):
    """Verify reading portfolio from CSV file with valid and invalid paths/columns."""
    csv_file = tmp_path / "valid_portfolio.csv"
    csv_file.write_text("Symbol,Company Name,Quantity,Average Price\nRELIANCE,Reliance Industries,10,2500\nTCS,Tata Consultancy Services,5,3500\n")

    res = read_portfolio.run(portfolio_file=str(csv_file))
    assert "Portfolio contains 2 stocks" in res
    assert "RELIANCE.NS" in res

    res_missing = read_portfolio.run(portfolio_file=str(tmp_path / "nonexistent.csv"))
    assert "Error: Portfolio file not found" in res_missing

    csv_invalid = tmp_path / "invalid_portfolio.csv"
    csv_invalid.write_text("Ticker,Qty\nRELIANCE,10\n")
    res_invalid = read_portfolio.run(portfolio_file=str(csv_invalid))
    assert "Error: Missing required columns" in res_invalid


# ==============================================================================
# 4. ROVER_TOOLS / GLOBAL_MARKET_TOOL.PY
# ==============================================================================
from rover_tools.global_market_tool import get_global_cues, get_global_cues_data

def test_get_global_cues_and_data():
    """Verify global cues string formatter and dictionary data retriever."""
    dates = pd.date_range(start="2024-01-01", periods=5, freq="D")
    df = pd.DataFrame({
        "CL=F": [75, 76, 77, 78, 79],
        "GC=F": [2000, 2010, 2020, 2030, 2040],
        "^NDX": [15000, 15100, 15200, 15300, 15400],
        "^GSPC": [4500, 4520, 4540, 4560, 4580],
        "INR=X": [83.0, 83.1, 83.2, 83.3, 83.4],
        "^VIX": [15, 14, 13, 14, 13],
        "^TNX": [4.1, 4.2, 4.1, 4.0, 4.1]
    }, index=dates)

    with patch("yfinance.download", return_value={"Close": df}):
        res_str = get_global_cues.run()
        assert "Global Market Cues" in res_str
        assert "Brent Crude" in res_str

    with patch("yfinance.download", side_effect=Exception("Failed")):
        res_err = get_global_cues.run()
        assert "Error fetching Global Market Cues" in res_err

    df_raw = pd.DataFrame({
        "^VIX": [15, 16],
        "^TNX": [4.1, 4.2],
        "DX-Y.NYB": [103, 104],
        "^GSPC": [4500, 4600]
    }, index=pd.date_range("2024-01-01", periods=2))
    with patch("yfinance.download", return_value={"Close": df_raw}):
        data = get_global_cues_data()
        assert isinstance(data, dict)
        assert "vix" in data
        assert "yield_10y" in data


# ==============================================================================
# 5. ROVER_TOOLS / FORENSIC_TOOL.PY
# ==============================================================================
from rover_tools.forensic_tool import check_accounting_fraud

def test_check_accounting_fraud():
    """Verify forensic accounting fraud checker tool."""
    with patch("rover_tools.forensic_tool.ForensicAnalyzer") as MockAnalyzer:
        instance = MockAnalyzer.return_value
        instance.generate_forensic_report.return_value = {
            "overall_status": "CLEAN",
            "checks": []
        }
        res_clean = check_accounting_fraud.run(ticker_symbol="TCS.NS")
        assert "FORENSIC AUDIT PASSED" in res_clean

    with patch("rover_tools.forensic_tool.ForensicAnalyzer") as MockAnalyzer:
        instance = MockAnalyzer.return_value
        instance.generate_forensic_report.return_value = {
            "overall_status": "HIGH_RISK",
            "checks": [
                {"metric": "Satyam Cash Check", "details": "Negative cash flow despite high revenue", "flag": "RED"}
            ]
        }
        res_risk = check_accounting_fraud.run(ticker_symbol="RISK.NS")
        assert "FORENSIC AUDIT WARNING" in res_risk
        assert "Satyam Cash Check" in res_risk

    with patch("rover_tools.forensic_tool.ForensicAnalyzer", side_effect=Exception("Crash")):
        res_err = check_accounting_fraud.run(ticker_symbol="ERR.NS")
        assert "Forensic Audit Error" in res_err


# ==============================================================================
# 6. ROVER_TOOLS / CORPORATE_ACTIONS_TOOL.PY
# ==============================================================================
from rover_tools.corporate_actions_tool import get_corporate_actions

def test_get_corporate_actions():
    """Verify corporate actions tool with NSE data."""
    mock_data = {
        "info": {"symbol": "RELIANCE"},
        "boardMeetings": [
            {"meetingDate": "2026-04-15", "purpose": "Financial Results & Dividend"}
        ]
    }
    with patch("rover_tools.corporate_actions_tool.nse_eq", return_value=mock_data):
        res = get_corporate_actions.run(symbol="RELIANCE.NS")
        assert "Corporate Actions for RELIANCE" in res
        assert "Financial Results & Dividend" in res

    with patch("rover_tools.corporate_actions_tool.nse_eq", return_value={}):
        res_empty = get_corporate_actions.run(symbol="EMPTY.NS")
        assert "No official corporate action data available" in res_empty

    with patch("rover_tools.corporate_actions_tool.nse_eq", side_effect=Exception("Blocked")):
        res_err = get_corporate_actions.run(symbol="BLOCK.NS")
        assert "Could not fetch official corporate actions" in res_err


# ==============================================================================
# 7. ROVER_TOOLS / SEARCH_TOOL.PY
# ==============================================================================
from rover_tools.search_tool import search_market_news

def test_search_market_news():
    """Verify search market news tool."""
    mock_results = [
        {"title": "RBI Keeps Repo Rate Unchanged", "body": "Monetary policy committee leaves rates steady.", "href": "https://news.example.com/rbi"}
    ]
    with patch("rover_tools.search_tool.DDGS") as MockDDGS:
        ddgs_inst = MagicMock()
        ddgs_inst.text.return_value = mock_results
        MockDDGS.return_value.__enter__.return_value = ddgs_inst

        res = search_market_news.run(query="RBI Repo Rate 2026")
        assert "Search Results for 'RBI Repo Rate 2026'" in res
        assert "RBI Keeps Repo Rate Unchanged" in res

    with patch("rover_tools.search_tool.DDGS") as MockDDGS:
        ddgs_inst = MagicMock()
        ddgs_inst.text.return_value = []
        MockDDGS.return_value.__enter__.return_value = ddgs_inst

        res_none = search_market_news.run(query="UnicornStock12345")
        assert "No search results found" in res_none

    with patch("rover_tools.search_tool.DDGS", side_effect=Exception("Search Error")):
        res_err = search_market_news.run(query="Fail")
        assert "Error performing search" in res_err


# ==============================================================================
# 8. ROVER_TOOLS / SRE_TOOLS.PY
# ==============================================================================
from rover_tools.sre_tools import propose_system_remediation

def test_propose_system_remediation(tmp_path):
    """Verify proposing system remediation creates HIL request."""
    temp_hil_file = tmp_path / "hil_requests.json"
    with patch("rover_tools.sre_tools.HIL_REQUESTS_FILE", temp_hil_file):
        msg = propose_system_remediation(
            issue_description="Database pool exhaustion",
            suggested_fix="Increase connection pool size to 50",
            risk_level="High"
        )
        assert "Governance Request" in msg
        assert temp_hil_file.exists()

        data = json.loads(temp_hil_file.read_text(encoding="utf-8"))
        assert len(data) == 1
        assert data[0]["agent_name"] == "SRE Support"
        assert data[0]["data"]["risk_level"] == "High"


# ==============================================================================
# 9. ROVER_TOOLS / AUTONOMY_TOOLS.PY
# ==============================================================================
from rover_tools.autonomy_tools import announce_regime_tool, log_pivot_tool

def test_autonomy_tools():
    """Verify autonomy decision logger tools."""
    with patch("rover_tools.autonomy_tools.log_autonomy_event") as mock_log:
        res_regime = announce_regime_tool.run(regime="GROWTH", reason="VIX is 12")
        assert "REGIME SET TO GROWTH" in res_regime
        mock_log.assert_called_once()

    with patch("rover_tools.autonomy_tools.log_autonomy_event") as mock_log:
        res_pivot = log_pivot_tool.run(missing_tool="Block Deals", pivot_tool="Sector Flow", reason="API down")
        assert "Pivot logged successfully" in res_pivot
        mock_log.assert_called_once()


# ==============================================================================
# 10. ROVER_TOOLS / HIL_CLIENT.PY
# ==============================================================================
from rover_tools.hil_client import notify_hil

def test_notify_hil():
    """Verify notify_hil client post and exception handling."""
    with patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "received", "id": "req_123"}
        mock_post.return_value = mock_resp

        res = notify_hil("SRE Sentinel", "Self-Test", "Instructions text")
        assert res["status"] == "received"

    with patch("requests.post", side_effect=Exception("Connection refused")):
        res_none = notify_hil("SRE", "Test", "Msg")
        assert res_none is None


# ==============================================================================
# 11. ROVER_TOOLS / HIL_GOVERNANCE.PY
# ==============================================================================
from rover_tools.hil_governance import (
    verify_action_with_human,
    check_decision_status,
    GovernanceError
)

def test_hil_governance_verify_and_check():
    """Verify HIL governance verification flow and status check."""
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        status = verify_action_with_human("PledgeCouncil", "Rebalance", {"ticker": "RELIANCE.NS"})
        assert status == "PENDING_HUMAN_REVIEW"

    with patch("requests.get", side_effect=Exception("Offline")):
        with pytest.raises(GovernanceError):
            verify_action_with_human("PledgeCouncil", "Rebalance", {})

    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "APPROVED"}
        mock_get.return_value = mock_resp

        res_stat = check_decision_status("req_123")
        assert res_stat == "APPROVED"

    with patch("requests.get", side_effect=Exception("Timeout")):
        assert check_decision_status("req_999") == "UNKNOWN"


# ==============================================================================
# 12. ROVER_TOOLS / MEMORY_TOOL.PY
# ==============================================================================
from rover_tools.memory_tool import (
    read_memory,
    write_memory,
    evaluate_pending_predictions,
    read_past_predictions_tool,
    save_prediction_tool
)

def test_memory_tool_crud_and_evaluation(tmp_path):
    """Verify memory tool persistence, evaluation, and retrieval."""
    temp_mem_file = str(tmp_path / "memory.json")
    with patch("rover_tools.memory_tool.MEMORY_FILE_PATH", temp_mem_file):
        assert read_memory() == []

        save_res = save_prediction_tool.run(ticker="INFY.NS", signal="Buy", confidence="High")
        assert "Saved prediction for INFY.NS" in save_res
        mem = read_memory()
        assert len(mem) == 1
        assert mem[0]["ticker"] == "INFY.NS"

        read_res = read_past_predictions_tool.run(ticker="INFY.NS")
        assert "Memory Recall" in read_res
        assert "Buy" in read_res

        read_none = read_past_predictions_tool.run(ticker="NONEXISTENT.NS")
        assert "No past history" in read_none

        mem[0]["date"] = (date.today() - timedelta(days=5)).isoformat()
        write_memory(mem)

        hist_df = pd.DataFrame({"Close": [1500, 1600]}, index=pd.date_range("2024-01-01", periods=2))
        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value.history.return_value = hist_df
            evaluate_pending_predictions()

        updated_mem = read_memory()
        assert updated_mem[0]["outcome"] == "Success"

def test_memory_tool_sell_predictions_and_errors(tmp_path):
    """Verify memory evaluation for bearish signals and error resilience."""
    temp_mem_file = str(tmp_path / "memory_bear.json")
    with patch("rover_tools.memory_tool.MEMORY_FILE_PATH", temp_mem_file):
        mem = [
            {
                "date": (date.today() - timedelta(days=5)).isoformat(),
                "ticker": "BEAR.NS",
                "signal": "Sell near resistance",
                "confidence": "Medium",
                "outcome": "Pending"
            },
            {
                "date": (date.today() - timedelta(days=5)).isoformat(),
                "ticker": "NEUTRAL.NS",
                "signal": "Hold / Sideways",
                "confidence": "Low",
                "outcome": "Pending"
            }
        ]
        write_memory(mem)

        # Drop in price -> Sell prediction is Success
        hist_df_drop = pd.DataFrame({"Close": [1000, 800]}, index=pd.date_range("2024-01-01", periods=2))
        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value.history.return_value = hist_df_drop
            evaluate_pending_predictions()

        evaluated = read_memory()
        assert evaluated[0]["outcome"] == "Success"
        assert evaluated[1]["outcome"] == "Neutral (No Direction)"


# ==============================================================================
# 13. ROVER_TOOLS / GENERATE_DAILY_REPORT.PY
# ==============================================================================
from rover_tools.generate_daily_report import generate_report

def test_generate_daily_report(tmp_path):
    """Verify generation of daily market intelligence markdown report."""
    hist_df = pd.DataFrame({"Close": [22000, 22200]}, index=pd.date_range("2024-01-01", periods=2))
    mock_sector_df = pd.DataFrame([
        {"Rank": 1, "Sector": "IT", "Momentum Score": 85.5, "1W %": 2.5, "1M %": 5.0}
    ])

    with patch("yfinance.Ticker") as MockTicker:
        MockTicker.return_value.history.return_value = hist_df
        with patch("rover_tools.generate_daily_report.analyze_sector_flow", return_value=mock_sector_df):
            with patch("builtins.open", MagicMock()):
                generate_report()


# ==============================================================================
# 14. ROVER_TOOLS / BATCH_BACKTESTER.PY
# ==============================================================================
from rover_tools.batch_backtester import (
    generate_email_summary,
    generate_markdown_report,
    run_batch_backtest
)

def test_batch_backtester_reports(tmp_path):
    """Verify backtester report generators for email and markdown."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    results_map = {
        "RELIANCE.NS": {
            "last_updated": today_str,
            "median_error": 5.2,
            "sd_error": 8.1,
            "winner": "median",
            "years_tested": [2021, 2022, 2023],
            "detailed_path": [
                {"date": "2024-01-01", "predicted_price": 2500, "actual_price": 2520, "error_pct": 0.8}
            ]
        },
        "TCS.NS": {
            "last_updated": today_str,
            "median_error": 25.0,
            "sd_error": 22.0,
            "winner": "sd",
            "years_tested": [2022, 2023],
            "detailed_path": []
        }
    }

    email_html = generate_email_summary(results_map, updated_count=2, failed_count=0)
    assert email_html is not None
    assert "Weekly Strategy Backtest Report" in email_html
    assert "RELIANCE.NS" in email_html
    assert generate_email_summary({}, 0, 0) is None

    with patch("builtins.open", MagicMock()):
        with patch("os.makedirs"):
            with patch("shutil.copy"):
                generate_markdown_report(results_map, updated_count=2, failed_count=0)

def test_run_batch_backtest():
    """Verify run_batch_backtest execution loop with mock fetcher and analyzer."""
    mock_data = pd.DataFrame({"Close": [100, 110, 120]}, index=pd.date_range("2020-01-01", periods=3, freq="MS"))
    with patch("rover_tools.batch_backtester.MarketDataFetcher") as MockFetcher:
        with patch("rover_tools.batch_backtester.MarketAnalyzer") as MockAnalyzer:
            with patch("rover_tools.batch_backtester.get_common_tickers", return_value=["RELIANCE.NS - Reliance"]):
                with patch("rover_tools.batch_backtester.evaluate_pending_predictions"):
                    with patch("builtins.open", MagicMock()):
                        with patch("os.makedirs"):
                            with patch("shutil.copy"):
                                run_batch_backtest()


# ==============================================================================
# 15. ROVER_TOOLS / MARKET_CONTEXT_TOOL.PY
# ==============================================================================
from rover_tools.market_context_tool import analyze_market_context

def test_analyze_market_context():
    """Verify market context analyzer tool with Nifty and sector tickers."""
    dates = pd.date_range("2024-01-01", periods=10)
    hist_df = pd.DataFrame({"Close": np.linspace(20000, 22000, 10)}, index=dates)

    with patch("yfinance.Ticker") as MockTicker:
        MockTicker.return_value.history.return_value = hist_df
        res = analyze_market_context.run(portfolio_stocks="TCS.NS,HDFCBANK.NS,MARUTI.NS")
        assert "Market Context Analysis" in res

def test_analyze_market_context_empty_and_failures():
    """Verify market context analyzer when history is empty or fails."""
    with patch("yfinance.Ticker") as MockTicker:
        MockTicker.return_value.history.return_value = pd.DataFrame()
        res = analyze_market_context.run(portfolio_stocks="")
        assert "Critical Market Data (Nifty 50) is unavailable" in res


# ==============================================================================
# 16. ROVER_TOOLS / VISMERA_CLIENT.PY
# ==============================================================================
from rover_tools.vismera_client import log_telemetry_event, get_vismera_status

def test_vismera_client():
    """Verify telemetry logging and status check in Vismera Platform client."""
    with patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "ok", "event_id": "evt_1"}
        mock_post.return_value = mock_resp

        res = log_telemetry_event("TEST_EVENT", "TestAgent", "sess_1", {"key": "val"})
        assert res["status"] == "ok"

    with patch("requests.post", side_effect=Exception("Timeout")):
        res_fb = log_telemetry_event("TEST_EVENT", "TestAgent", "sess_1", {})
        assert res_fb["status"] == "sandbox_logged"

    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"api": "operational"}
        mock_get.return_value = mock_resp

        stat = get_vismera_status()
        assert stat["status"] == "healthy"

    with patch("rover_tools.vismera_client.VISMERA_ENABLED", False):
        stat_dis = get_vismera_status()
        assert stat_dis["status"] == "disabled"


# ==============================================================================
# 17. ROVER_TOOLS / STOCK_DATA_TOOL.PY
# ==============================================================================
from rover_tools.stock_data_tool import get_stock_data

def test_get_stock_data():
    """Verify get_stock_data tool with mock yfinance info and history."""
    dates = pd.date_range("2023-01-01", periods=250, freq="D")
    hist_df = pd.DataFrame({
        "Close": np.linspace(2500, 2900, 250),
        "High": np.linspace(2550, 2950, 250),
        "Low": np.linspace(2450, 2850, 250)
    }, index=dates)

    with patch("yfinance.Ticker") as MockTicker:
        mock_inst = MockTicker.return_value
        mock_inst.info = {
            "currentPrice": 2900.0,
            "previousClose": 2850.0,
            "marketCap": 19500000000000,
            "sector": "Energy",
            "industry": "Oil & Gas"
        }
        mock_inst.history.return_value = hist_df

        res = get_stock_data.run(symbol="RELIANCE.NS")
        assert "Stock Data for RELIANCE.NS" in res
        assert "Current Price: ₹2900.00" in res
        assert "Sector: Energy" in res

    # Empty history
    with patch("yfinance.Ticker") as MockTicker:
        mock_inst = MockTicker.return_value
        mock_inst.info = {}
        mock_inst.history.return_value = pd.DataFrame()

        res_empty = get_stock_data.run(symbol="EMPTY.NS")
        assert "No data available" in res_empty

    # Exception
    with patch("yfinance.Ticker", side_effect=Exception("Ticker failure")):
        res_err = get_stock_data.run(symbol="FAIL.NS")
        assert "Error fetching stock data" in res_err or "Error fetching data" in res_err


# ==============================================================================
# 18. ROVER_TOOLS / NEWS_SCRAPER_TOOL.PY
# ==============================================================================
from rover_tools.news_scraper_tool import (
    scrape_general_market_news,
    scrape_stock_news,
    async_scrape_stock_run,
    fetch_url,
    extract_links_from_search,
    process_article
)

def test_scrape_general_market_news():
    """Verify general market news scraping with mocked HTML response."""
    mock_html = """
    <html><body>
        <a href="https://www.moneycontrol.com/news/business/reliance-q4-results-revenue-beats-estimates.html">
            Reliance Q4 Results: Consolidated Revenue Beats Estimates by 5 Percent
        </a>
        <a href="https://www.moneycontrol.com/news/business/tcs-signs-mega-deal-cloud-transformation.html">
            TCS Signs Multi-Billion Dollar Deal for Cloud Transformation in Europe
        </a>
    </body></html>
    """
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = mock_html.encode("utf-8")
        mock_get.return_value = mock_resp

        res = scrape_general_market_news.run(category="business")
        assert "Top Market Headlines (business)" in res
        assert "Reliance Q4 Results" in res

    # 500 error
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_get.return_value = mock_resp

        res_fail = scrape_general_market_news.run(category="markets")
        assert "Failed to fetch news" in res_fail

    # Connection failure
    with patch("requests.get", side_effect=Exception("ConnectTimeout")):
        res_err = scrape_general_market_news.run()
        assert "Failed to connect to news source" in res_err

@pytest.mark.asyncio
async def test_scrape_stock_news_helpers():
    """Verify async stock news helper functions."""
    # 1. fetch_url
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "<html>Sample Content</html>"
        mock_get.return_value = mock_resp

        content = await fetch_url("https://www.moneycontrol.com/news/test")
        assert "Sample Content" in content

    # 2. extract_links_from_search
    sample_search_html = """
    <html><body>
        <a href="https://www.moneycontrol.com/news/business/infy-earnings-12345.html">Infosys Earnings</a>
        <a href="/news/markets/infy-outlook-67890.html">Infosys Outlook</a>
    </body></html>
    """
    with patch("rover_tools.news_scraper_tool.fetch_url", return_value=sample_search_html):
        links = await extract_links_from_search("INFY.NS")
        assert len(links) >= 1
        assert "https://www.moneycontrol.com" in links[0] or "/news/" in links[0]

    # 3. process_article
    with patch("rover_tools.news_scraper_tool.Article") as MockArticle:
        art_inst = MagicMock()
        art_inst.title = "Infosys Wins Cloud Deal"
        art_inst.text = "Infosys has announced a multi-year deal."
        art_inst.publish_date = datetime.now() - timedelta(days=1)
        MockArticle.return_value = art_inst

        art_data = await process_article("https://www.moneycontrol.com/news/deal", datetime.now() - timedelta(days=7))
        assert art_data is not None
        assert art_data["title"] == "Infosys Wins Cloud Deal"

    # 4. async_scrape_stock_run
    with patch("rover_tools.news_scraper_tool.extract_links_from_search", return_value=["https://www.moneycontrol.com/news/1"]):
        with patch("rover_tools.news_scraper_tool.process_article", return_value={"title": "Stock Up", "summary": "Positive earnings", "date": "2026-03-01"}):
            output = await async_scrape_stock_run("INFY.NS")
            assert "Context: Found 1 articles for INFY.NS" in output
            assert "Stock Up" in output


# ==============================================================================
# 19. SERVER.PY (UNIFIED ENTRY GATEWAY)
# ==============================================================================
import server

test_server_client = TestClient(server.app)

def test_server_health_endpoints():
    """Verify unified health check endpoints on server.py."""
    res1 = test_server_client.get("/health")
    assert res1.status_code == 200
    assert res1.json()["status"] == "healthy"

    res2 = test_server_client.get("/api/v1/health")
    assert res2.status_code == 200
    assert "market_rover" in res2.json()["services"]

    res3 = test_server_client.get("/api/v1/vismera/status")
    assert res3.status_code == 200
    assert "status" in res3.json()

    res4 = test_server_client.get("/api/v1/vismera/user", headers={"Authorization": "Bearer mock_jwt_token"})
    assert res4.status_code == 200

def test_server_analyze_get_and_post():
    """Verify /api/v1/market/analyze GET and POST endpoints."""
    res_get = test_server_client.get("/api/v1/market/analyze")
    assert res_get.status_code == 200
    assert res_get.json()["status"] == "OPERATIONAL"

    with patch("crew_engine.MarketRoverCrew") as MockCrew:
        crew_inst = MockCrew.return_value
        crew_inst.run_async = AsyncMock(return_value="Detailed Market Analysis Completed")

        res_post = test_server_client.post("/api/v1/market/analyze", json={
            "tickers": ["RELIANCE.NS"],
            "query": "Full analysis"
        })
        assert res_post.status_code == 200
        data = res_post.json()
        assert data["status"] == "success"
        assert data["agent"] == "MarketRoverCrew"

    with patch("crew_engine.MarketRoverCrew", side_effect=Exception("Crew Error")):
        with patch("rover_tools.batch_tools.batch_get_stock_data", return_value={"RELIANCE.NS": {"price": "2980", "50_dma": "2900", "rsi": "60"}}):
            res_fb = test_server_client.post("/api/v1/market/analyze", json={
                "tickers": ["RELIANCE.NS"]
            })
            assert res_fb.status_code == 200
            data_fb = res_fb.json()
            assert data_fb["status"] == "success"
            assert data_fb["agent"] == "MarketRoverCrew_Fallback"

def test_server_spa_and_static_routing(tmp_path):
    """Verify SPA catch-all and static asset 404 behavior."""
    res_api_404 = test_server_client.get("/api/unknown_route_12345")
    assert res_api_404.status_code == 404

    res_asset_404 = test_server_client.get("/static/nonexistent_bundle.js")
    assert res_asset_404.status_code == 404

    res_root = test_server_client.get("/")
    assert res_root.status_code == 200

    res_hil = test_server_client.get("/hil")
    assert res_hil.status_code == 200


# ==============================================================================
# 20. PLEDGE_ROVER / AGENTS / HARVESTER.PY
# ==============================================================================
from pledge_rover.backend.src.agents.harvester import ExchangeHarvester

@pytest.mark.asyncio
async def test_exchange_harvester_all_branches():
    """Verify exchange harvester with successful BSE/NSE payloads, decoding errors, and merge logic."""
    harvester = ExchangeHarvester()

    mock_bse_res = MagicMock()
    mock_bse_res.status_code = 200
    mock_bse_res.json.return_value = {
        "Table": [
            {
                "scripcode": "500325",
                "scripname": "Reliance Industries",
                "Pledgor_Name": "Promoter Trust",
                "Pledgee_Name": "State Bank of India",
                "Total_Pledge_Shares_Per": "2.5",
                "Date_of_Transaction": "2026-03-01"
            }
        ]
    }

    mock_nse_res = MagicMock()
    mock_nse_res.status_code = 200
    mock_nse_res.json.return_value = {
        "data": [
            ["RELIANCE", "Reliance Industries", "Promoter Trust", "01-Mar-2026", "", "", "", "3.0"]
        ]
    }

    with patch("httpx.AsyncClient.get", side_effect=[mock_bse_res, MagicMock(status_code=200), mock_nse_res]):
        combined = await harvester.get_7_day_combined_feed()
        assert len(combined) >= 1
        assert combined[0]["symbol"] in ["500325", "RELIANCE"]

    with patch("httpx.AsyncClient.get", side_effect=Exception("Connection Reset")):
        bse_fallback = await harvester.fetch_bse_recent_pledges()
        assert len(bse_fallback) >= 5

    with patch("httpx.AsyncClient.get", side_effect=Exception("Blocked")):
        nse_fallback = await harvester.fetch_nse_recent_pledges()
        assert len(nse_fallback) >= 5


# ==============================================================================
# 21. PLEDGE_ROVER / CONFIG / DATABASE.PY
# ==============================================================================
import pledge_rover.backend.src.config.database as pr_db

@pytest.mark.asyncio
async def test_pledge_rover_db_lifecycle():
    """Verify pledge rover database initialization and teardown."""
    mock_engine = MagicMock()
    mock_conn = AsyncMock()
    mock_engine.begin.return_value.__aenter__.return_value = mock_conn
    mock_engine.dispose = AsyncMock()

    with patch.object(pr_db, "engine", mock_engine):
        await pr_db.init_db()
        mock_conn.run_sync.assert_called_once()
        await pr_db.close_db()
        mock_engine.dispose.assert_called_once()


# ==============================================================================
# 22. MARKET_ROVER / UTILS / DB_MANAGER.PY
# ==============================================================================
from src.utils.db_manager import DBManager

@pytest.mark.asyncio
async def test_db_manager_crud_and_connections():
    """Verify DBManager connection provisioning and query helper methods."""
    manager = DBManager()

    mock_pool = MagicMock()
    mock_conn = AsyncMock()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

    with patch("asyncpg.create_pool", new_callable=AsyncMock, return_value=mock_pool):
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost:5432/testdb"}):
            await manager.connect()
            assert manager.pool is not None

        await manager.log_activity("user_1", "LOGIN", "WEB")
        mock_conn.execute.assert_called()

        await manager.set_user_persona("user_1", "Aggressive")
        mock_conn.fetchval.return_value = "Aggressive"
        prof = await manager.get_user_persona("user_1")
        assert prof == "Aggressive"

        await manager.store_memory("user_1", "TCS.NS", "BULLISH", "Strong earnings")
        mock_conn.fetchrow.return_value = {"stance": "BULLISH", "logic_summary": "Strong earnings"}
        ltm = await manager.get_memory("user_1", "TCS.NS")
        assert ltm["stance"] == "BULLISH"

        await manager.record_share("user_1", "TWITTER", "CARD", 5)

        mock_conn.fetch.return_value = [{"ticker": "TCS.NS", "stance": "BULLISH"}]
        history = await manager.get_forecast_history("user_1")
        assert len(history) == 1

    manager_fail = DBManager()
    with patch("asyncpg.create_pool", side_effect=Exception("DB Down")):
        await manager_fail.connect()
        assert manager_fail.pool is None
        await manager_fail.log_activity("u", "a")
        assert await manager_fail.get_user_persona("u") is None
        assert await manager_fail.get_memory("u", "t") is None
        assert await manager_fail.get_forecast_history("u") == []


# ==============================================================================
# 23. MARKET_ROVER / UTILS / THROTTLE.PY
# ==============================================================================
from src.utils.throttle import throttled, gather_with_concurrency

@pytest.mark.asyncio
async def test_throttled_decorator_and_concurrency():
    """Verify @throttled retry mechanism and gather_with_concurrency."""
    call_count = 0

    @throttled
    async def flaky_api(symbol: str):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise Exception("Rate limit exceeded 429: Too Many Requests")
        return f"Data for {symbol}"

    res = await flaky_api("INFY.NS")
    assert res == "Data for INFY.NS"
    assert call_count == 2

    @throttled
    async def failing_func():
        raise ValueError("Invalid symbol format")

    with pytest.raises(ValueError):
        await failing_func()

    async def sample_task(x):
        return x * 2

    results = await gather_with_concurrency(2, sample_task(1), sample_task(2), sample_task(3))
    assert results == [2, 4, 6]


# ==============================================================================
# 24. ROVER_TOOLS / MARKET_DATA.PY
# ==============================================================================
from rover_tools.market_data import MarketDataFetcher

def test_market_data_fetcher_all_branches():
    """Verify MarketDataFetcher LTP, historical data, full history, and option chains."""
    fetcher = MarketDataFetcher()

    with patch.object(fetcher, "_fetch_yf_price_unsafe", return_value=22500.0):
        ltp_index = fetcher.fetch_ltp("^NSEI")
        assert ltp_index == 22500.0

    with patch.object(fetcher, "_fetch_yf_price_unsafe", side_effect=[Exception("NSE Down"), 2500.0]):
        ltp_stock = fetcher.fetch_ltp("RELIANCE.NS")
        assert ltp_stock == 2500.0

    with patch.object(fetcher, "_fetch_yf_price_unsafe", side_effect=Exception("All Down")):
        ltp_none = fetcher.fetch_ltp("FAIL.NS")
        assert ltp_none is None

    dates = pd.date_range("2024-01-01", periods=5)
    hist_df = pd.DataFrame({"Close": [100, 102, 104, 106, 108]}, index=dates)

    with patch.object(fetcher, "_fetch_yf_history_unsafe", return_value=hist_df):
        hist_index = fetcher.fetch_historical_data("^NSEI")
        assert not hist_index.empty

    with patch.object(fetcher, "_fetch_yf_history_unsafe", side_effect=[Exception("NSE Fail"), hist_df]):
        hist_stock = fetcher.fetch_historical_data("TCS.NS")
        assert not hist_stock.empty

    with patch.object(fetcher, "fetch_historical_data", return_value=hist_df):
        full_hist = fetcher.fetch_full_history("INFY.NS")
        assert not full_hist.empty

    with patch("rover_tools.market_data.nse_optionchain_scrapper", return_value={"records": {"data": []}}):
        chain = fetcher.fetch_option_chain("NIFTY.NS")
        assert chain is not None

    with patch("rover_tools.market_data.nse_optionchain_scrapper", side_effect=Exception("Scraper Error")):
        chain_none = fetcher.fetch_option_chain("FAIL.NS")
        assert chain_none is None
