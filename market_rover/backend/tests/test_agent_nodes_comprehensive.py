"""
test_agent_nodes_comprehensive.py — Exhaustive Unit Test Suite for All 11 LangGraph Agent Nodes.
Covers happy paths, branch divergences, and exception fallbacks.
"""
import pytest
import pandas as pd
from unittest.mock import AsyncMock, MagicMock, patch

from market_rover.backend.src.agents.dividend_node import dividend_node, get_ticker_dividend
from market_rover.backend.src.agents.forensic_node import forensic_node
from market_rover.backend.src.agents.ownerise_node import ownerise_node
from market_rover.backend.src.agents.reporting_node import reporting_node
from market_rover.backend.src.agents.retrieval_node import retrieval_node
from market_rover.backend.src.agents.sector_node import sector_node
from market_rover.backend.src.agents.sentiment_node import sentiment_node, get_ticker_sentiment
from market_rover.backend.src.agents.shadow_node import shadow_node
from market_rover.backend.src.agents.strategy_node import strategy_node
from market_rover.backend.src.agents.technical_node import technical_node, analyze_ticker_technicals
from market_rover.backend.src.agents.traditional_node import traditional_node


# ── 1. Retrieval Node Tests ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_retrieval_node_clean_and_ltm():
    state = {
        "tickers": ["tcs", "infy", "reliance", "sbin", "itc", "invalidtoolongtickername123", "a"],
        "discoverable_handle": "test_user"
    }
    with patch("market_rover.backend.src.agents.retrieval_node.db") as mock_db:
        mock_db.connect = AsyncMock()
        mock_db.get_memory = AsyncMock(side_effect=lambda user, t: {
            "stance": "BULLISH",
            "logic_summary": "Strong quarterly momentum",
            "analysis_date": pd.Timestamp("2026-09-01")
        } if t == "TCS.NS" else None)

        res = await retrieval_node(state)
        assert "TCS.NS" in res["tickers"]
        assert "INFY.NS" in res["tickers"]
        assert len(res["celebrations"]) > 0
        assert res["celebrations"][0]["type"] == "CONFETTI_LOW"
        assert len(res["feedback_prompts"]) > 0
        assert res["feedback_prompts"][0]["type"] == "TICKER_FIX"
        assert "TCS.NS" in res["historical_stances"]


@pytest.mark.asyncio
async def test_retrieval_node_fallback_csv_success():
    state = {}
    with patch("market_rover.backend.src.agents.retrieval_node.read_portfolio") as mock_port, \
         patch("market_rover.backend.src.agents.retrieval_node.db") as mock_db:
        mock_port.run.return_value = [{"ticker": "HDFCBANK.NS"}]
        mock_db.connect = AsyncMock()
        mock_db.get_memory = AsyncMock(return_value=None)

        res = await retrieval_node(state)
        assert res["tickers"] == ["HDFCBANK.NS"]


@pytest.mark.asyncio
async def test_retrieval_node_fallback_csv_failure():
    state = {}
    with patch("market_rover.backend.src.agents.retrieval_node.read_portfolio") as mock_port:
        mock_port.run.side_effect = Exception("CSV Not Found")
        res = await retrieval_node(state)
        assert "errors" in res
        assert "Portfolio Retrieval Failed" in res["errors"][0]


# ── 2. Traditional Node Tests ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_traditional_node_undervalued_and_muhurta():
    state = {"tickers": ["TATAMOTORS.NS", "ITC.NS"]}
    with patch("market_rover.backend.src.agents.traditional_node.fetch_subha_muhurtham_tool") as mock_muhurta, \
         patch("market_rover.backend.src.agents.traditional_node.yf.Ticker") as mock_yf:
        mock_muhurta.run.return_value = "Auspicious window on Akshaya Tritiya 2026."

        inst = MagicMock()
        inst.info = {"trailingPE": 14.5, "pegRatio": 0.85, "priceToBook": 1.8}
        mock_yf.return_value = inst

        res = await traditional_node(state)
        assert len(res["fundamental_data"]) == 2
        assert res["fundamental_data"][0]["is_undervalued"] is True
        assert any(c["type"] == "TRADITIONAL_DIYA" for c in res["celebrations"])
        assert any(c["type"] == "VALUE_GEM_GLOW" for c in res["celebrations"])


@pytest.mark.asyncio
async def test_traditional_node_error_handling():
    state = {"tickers": ["FAIL.NS"]}
    with patch("market_rover.backend.src.agents.traditional_node.fetch_subha_muhurtham_tool") as mock_muhurta, \
         patch("market_rover.backend.src.agents.traditional_node.yf.Ticker") as mock_yf:
        mock_muhurta.run.return_value = "Normal trading window."
        mock_yf.side_effect = Exception("Ticker fetch error")

        res = await traditional_node(state)
        assert res["fundamental_data"][0]["status"] == "Fundamental Data Unavailable"


# ── 3. Technical Node Tests ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_technical_node_empty():
    res = await technical_node({})
    assert res["technical_data"] == []


@pytest.mark.asyncio
async def test_technical_node_strong_concordance():
    state = {"tickers": ["RELIANCE.NS"]}
    with patch("market_rover.backend.src.agents.technical_node.calculate_mtc_score_tool") as mock_mtc, \
         patch("market_rover.backend.src.agents.technical_node.detect_technical_patterns_tool") as mock_pat:
        mock_mtc.run.return_value = "STRONG BUY CONCORDANCE [85/100]"
        mock_pat.run.return_value = "Bull Flag Breakout"

        res = await technical_node(state)
        assert res["technical_data"][0]["concordance"] == "Strong"
        assert any(c["type"] == "TRIPLE_PULSE_ACTION" for c in res["celebrations"])


@pytest.mark.asyncio
async def test_technical_node_divergence():
    state = {"tickers": ["INFY.NS"]}
    with patch("market_rover.backend.src.agents.technical_node.calculate_mtc_score_tool") as mock_mtc, \
         patch("market_rover.backend.src.agents.technical_node.detect_technical_patterns_tool") as mock_pat:
        mock_mtc.run.return_value = "NEUTRAL [50/100]"
        mock_pat.run.return_value = "No pattern"

        res = await technical_node(state)
        assert res["technical_data"][0]["concordance"] == "None"
        assert any(f["type"] == "DIVERGENCE_REVIEW" for f in res["feedback_prompts"])


@pytest.mark.asyncio
async def test_technical_node_error():
    with patch("market_rover.backend.src.agents.technical_node.calculate_mtc_score_tool") as mock_tool:
        mock_tool.run.side_effect = Exception("Technical Tool Failure")
        res = await analyze_ticker_technicals("FAIL.NS")
        assert res["concordance"] == "Data Unavailable"


# ── 4. Sentiment Node Tests ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sentiment_node_empty():
    res = await sentiment_node({})
    assert res["sentiment_data"] == []


@pytest.mark.asyncio
async def test_sentiment_node_bullish_cluster():
    state = {"tickers": ["TCS.NS"]}
    with patch("market_rover.backend.src.agents.sentiment_node.yf.Ticker") as mock_yf:
        inst = MagicMock()
        inst.news = [
            {"title": "TCS reports massive profit growth and strong gain in digital revenue"},
            {"title": "Positive expansion announced"}
        ]
        mock_yf.return_value = inst

        res = await sentiment_node(state)
        assert res["sentiment_data"][0]["sentiment"] == "positive"
        assert any(c["type"] == "CROWD_CHEER" for c in res["celebrations"])


@pytest.mark.asyncio
async def test_sentiment_node_bearish_and_neutral():
    with patch("market_rover.backend.src.agents.sentiment_node.yf.Ticker") as mock_yf:
        inst = MagicMock()
        inst.news = [{"title": "Big loss, warning and decline in sales"}]
        mock_yf.return_value = inst
        bearish_res = await get_ticker_sentiment("BEAR.NS")
        assert bearish_res["sentiment"] == "negative"

        inst.news = [{"title": "Company holds annual general meeting"}]
        neutral_res = await get_ticker_sentiment("NEUT.NS")
        assert neutral_res["sentiment"] == "neutral"

        mock_yf.side_effect = Exception("API error")
        err_res = await get_ticker_sentiment("ERR.NS")
        assert err_res["sentiment"] == "Data Unavailable"


# ── 5. Forensic Node Tests ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_forensic_node_healthy_and_critical():
    state = {"tickers": ["SAFE.NS", "RISKY.NS"]}
    with patch("market_rover.backend.src.agents.forensic_node.ForensicAnalyzer") as mock_analyzer_cls:
        def get_analyzer(ticker):
            inst = MagicMock()
            if ticker == "RISKY.NS":
                inst.generate_forensic_report.return_value = {
                    "overall_status": "CRITICAL",
                    "red_flags": 3,
                    "summary": "High debt and aggressive revenue recognition"
                }
            else:
                inst.generate_forensic_report.return_value = {
                    "overall_status": "HEALTHY",
                    "red_flags": 0,
                    "summary": "Clean accounting"
                }
            return inst

        mock_analyzer_cls.side_effect = get_analyzer
        res = await forensic_node(state)
        assert len(res["forensic_reports"]) == 2
        assert any(c["type"] == "FORENSIC_ALERT_FLARE" for c in res["celebrations"])
        assert any(f["type"] == "RISK_MITIGATION_CHOICE" for f in res["feedback_prompts"])


@pytest.mark.asyncio
async def test_forensic_node_exception():
    state = {"tickers": ["ERR.NS"]}
    with patch("market_rover.backend.src.agents.forensic_node.ForensicAnalyzer", side_effect=Exception("Crash")):
        res = await forensic_node(state)
        assert res["forensic_reports"][0]["status"] == "Error"


# ── 6. Shadow Node Tests ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_shadow_node_all_branches():
    state = {
        "sentiment_data": [
            {"ticker": "ABSORB.NS", "sentiment": "negative"},
            {"ticker": "DISTRIB.NS", "sentiment": "positive"},
            {"ticker": "GHOST.NS", "sentiment": "neutral"},
            {"ticker": "ORPHAN.NS", "sentiment": "positive"}
        ],
        "technical_data": [
            {"ticker": "ABSORB.NS", "concordance": "Strong"},
            {"ticker": "DISTRIB.NS", "concordance": "None"},
            {"ticker": "GHOST.NS", "concordance": "Strong"}
        ],
        "forensic_reports": [
            {"ticker": "GHOST.NS", "status": "CRITICAL", "summary": "Audit discrepancy"}
        ]
    }
    res = await shadow_node(state)
    assert any("INSTITUTIONAL ABSORPTION" in s for s in res["shadow_signals"])
    assert any("DISTRIBUTION TRAP" in s for s in res["shadow_signals"])
    assert any("FORENSIC GHOST" in s for s in res["shadow_signals"])
    assert any(c["type"] == "FORENSIC_DISCOVERY_FLARE" for c in res["celebrations"])
    assert any(f["type"] == "DEEP_DIVE_REQUEST" for f in res["feedback_prompts"])


# ── 7. Sector Node Tests ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sector_node_aligned():
    state = {"tickers": ["TCS.NS", "INFY.NS"]}
    with patch("market_rover.backend.src.agents.sector_node.analyze_sector_flow_tool") as mock_tool:
        mock_tool.run.return_value = "IT sector is the leading sector this month."
        res = await sector_node(state)
        assert any(c["type"] == "SECTOR_LEADER_PULSE" for c in res["celebrations"])


# ── 8. Dividend Node Tests ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_dividend_node_empty():
    res = await dividend_node({})
    assert res["dividend_data"] == []


@pytest.mark.asyncio
async def test_dividend_node_high_and_low_yield():
    state = {"tickers": ["HIGH.NS", "LOW.NS"]}
    with patch("market_rover.backend.src.agents.dividend_node.yf.Ticker") as mock_yf:
        def get_stock(t):
            inst = MagicMock()
            if t == "HIGH.NS":
                inst.info = {"dividendYield": 0.045, "payoutRatio": 0.7}
            else:
                inst.info = {"dividendYield": 0.01, "payoutRatio": 0.2}
            return inst

        mock_yf.side_effect = get_stock
        res = await dividend_node(state)
        assert any(c["type"] == "YIELD_WINNER_BANNER" for c in res["celebrations"])

        mock_yf.side_effect = Exception("Dividend API Down")
        err_res = await get_ticker_dividend("ERR.NS")
        assert err_res["yield"] == "Data Unavailable"


# ── 9. Ownerise Node Tests ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ownerise_node_hit_and_miss():
    state_hit = {"tickers": ["RELIANCE.NS"]}
    res_hit = await ownerise_node(state_hit)
    assert any(c["type"] == "OWNERISE_ALERT" for c in res_hit["celebrations"])
    assert len(res_hit["traditional_insights"]) > 0

    state_miss = {"tickers": ["TCS.NS"]}
    res_miss = await ownerise_node(state_miss)
    assert "celebrations" not in res_miss or len(res_miss.get("celebrations", [])) == 0


# ── 10. Strategy Node Tests ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_strategy_node_regimes():
    with patch("market_rover.backend.src.agents.strategy_node.get_global_cues_data") as mock_cues:
        # Goldilocks
        mock_cues.return_value = {"vix": 14.0, "dxy": 99.0, "yield_10y": 3.8}
        res_gold = await strategy_node({})
        assert res_gold["regime"] == "GOLDILOCKS"
        assert any(c["type"] == "GLOW_SUCCESS" for c in res_gold["celebrations"])

        # Panic
        mock_cues.return_value = {"vix": 28.0, "dxy": 105.0, "yield_10y": 4.5}
        res_panic = await strategy_node({})
        assert res_panic["regime"] == "DEFLATIONARY / PANIC"
        assert any(f["type"] == "RISK_ALERT" for f in res_panic["feedback_prompts"])

        # Reflation
        mock_cues.return_value = {"vix": 21.0, "dxy": 102.0, "yield_10y": 4.2}
        res_refl = await strategy_node({})
        assert res_refl["regime"] == "REFLATION / GROWTH"
        assert any(c["type"] == "PULSE_ACTION" for c in res_refl["celebrations"])

        # Exception
        mock_cues.side_effect = Exception("Macro API down")
        res_err = await strategy_node({})
        assert "errors" in res_err


# ── 11. Reporting Node Tests ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_reporting_node_full_synthesis():
    state = {
        "regime": "GOLDILOCKS",
        "shadow_signals": ["Trap detected in TCS.NS"],
        "institutional_intent": "ACCUMULATION",
        "macro_context": "Global cues steady.",
        "technical_data": [{"ticker": "TCS.NS", "concordance": "Strong"}],
        "fundamental_data": [{"ticker": "TCS.NS", "pe": "24.5"}],
        "dividend_data": [{"ticker": "TCS.NS", "yield": "2.5%"}],
        "sector_data": [{"report": "IT leading"}],
        "traditional_insights": ["Akshaya Tritiya window"],
        "discoverable_handle": "sankar",
        "tickers": ["TCS.NS"]
    }
    with patch("market_rover.backend.src.agents.reporting_node.db") as mock_db:
        mock_db.connect = AsyncMock()
        mock_db.store_memory = AsyncMock()
        mock_db.log_activity = AsyncMock()

        res = await reporting_node(state)
        assert "# Market-Rover Intelligence Report" in res["final_report"]
        assert any(c["type"] == "FINAL_CONFETTI_BURST" for c in res["celebrations"])
        assert any(f["type"] == "RATE_REPORT" for f in res["feedback_prompts"])
        mock_db.store_memory.assert_awaited_once()
        mock_db.log_activity.assert_awaited_once()
