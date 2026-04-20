import pytest
from unittest.mock import AsyncMock, patch
from src.agents.strategy_node import strategy_node
from src.agents.sentiment_node import sentiment_node
from src.agents.technical_node import technical_node
from src.agents.shadow_node import shadow_node
from src.agents.dividend_node import dividend_node
from src.agents.sector_node import sector_node
from src.agents.reporting_node import reporting_node

@pytest.fixture
def base_state():
    return {
        "tickers": ["TCS.NS"],
        "regime": "NEUTRAL",
        "sentiment_data": [],
        "technical_data": [],
        "celebrations": [],
        "feedback_prompts": []
    }

# --- Strategy Node Tests ---
@pytest.mark.asyncio
async def test_strategy_node_goldilocks(base_state):
    with patch("src.agents.strategy_node.get_global_cues_data") as mock_cues:
        mock_cues.return_value = {"vix": 15, "dxy": 101, "yield_10y": 3.5}
        result = await strategy_node(base_state)
        assert result["regime"] == "GOLDILOCKS"
        assert any(c["type"] == "GLOW_SUCCESS" for c in result["celebrations"])

@pytest.mark.asyncio
async def test_strategy_node_panic(base_state):
    with patch("src.agents.strategy_node.get_global_cues_data") as mock_cues:
        mock_cues.return_value = {"vix": 30, "dxy": 105, "yield_10y": 4.5}
        result = await strategy_node(base_state)
        assert "PANIC" in result["regime"]
        assert any(f["type"] == "RISK_ALERT" for f in result["feedback_prompts"])

# --- Sentiment Node Tests ---
@pytest.mark.asyncio
async def test_sentiment_node_consensus(base_state):
    with patch("yfinance.Ticker") as mock_yf:
        # Simulate majority bullish news to trigger consensus
        mock_yf.return_value.news = [
            {"title": "gain surge growth positive profit"}
        ] * 5
        result = await sentiment_node(base_state)
        assert len(result["sentiment_data"]) == 1

# --- Technical Node Tests ---
@pytest.mark.asyncio
async def test_technical_node_triple_concordance(base_state):
    with patch("src.agents.technical_node.calculate_mtc_score_tool") as mock_mtc:
        with patch("src.agents.technical_node.detect_technical_patterns_tool") as mock_pat:
            mock_mtc.return_value = "STRONG BUY CONCORDANCE [85/100]"
            mock_pat.return_value = "Cup and Handle detected."
            result = await technical_node(base_state)
            assert result["technical_data"][0]["concordance"] == "Strong"
            assert any(c["type"] == "TRIPLE_PULSE_ACTION" for c in result["celebrations"])

# --- Shadow Node Tests ---
@pytest.mark.asyncio
async def test_shadow_node_trap_detection(base_state):
    base_state["sentiment_data"] = [{"ticker": "TCS.NS", "sentiment": "negative"}]
    base_state["technical_data"] = [{"ticker": "TCS.NS", "concordance": "Strong"}]
    result = await shadow_node(base_state)
    assert result["institutional_intent"] == "ACCUMULATION"
    assert any(c["type"] == "FORENSIC_DISCOVERY_FLARE" for c in result["celebrations"])

# --- Dividend Node Tests ---
@pytest.mark.asyncio
async def test_dividend_node_yield(base_state):
    with patch("src.agents.dividend_node.yf.Ticker") as mock_yf:
        mock_yf.return_value.info = {"dividendYield": 0.05, "payoutRatio": 0.6}
        result = await dividend_node(base_state)
        assert result["dividend_data"][0]["yield"] == "5.00%"
        assert any(c["type"] == "YIELD_WINNER_BANNER" for c in result["celebrations"])

# --- Sector Node Tests ---
@pytest.mark.asyncio
async def test_sector_node_alignment(base_state):
    with patch("rover_tools.shadow_tools.analyze_sector_flow_tool",
               return_value="Market LEADING breakout in IT sector."):
        result = await sector_node(base_state)
        # sector node calls the stub — verify it returns sector_data
        assert "sector_data" in result or "celebrations" in result

# --- Reporting Node Tests ---
@pytest.mark.asyncio
async def test_reporting_node_synthesis(base_state):
    base_state["regime"] = "GOLDILOCKS"
    base_state["shadow_signals"] = ["Trap detected"]
    with patch("src.agents.reporting_node.db") as mock_db:
        mock_db.connect = AsyncMock()
        mock_db.store_memory = AsyncMock()
        mock_db.log_activity = AsyncMock()
        result = await reporting_node(base_state)
        assert "# Market-Rover Intelligence Report" in result["final_report"]
        assert any(c["type"] == "FINAL_CONFETTI_BURST" for c in result["celebrations"])
