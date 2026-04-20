import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from src.state import AgentState
from src.agents.retrieval_node import retrieval_node

# 1. SETUP: Mock State
@pytest.fixture
def base_state():
    return {
        "tickers": ["TCS", "RELIANCE", "Invalid_Ticker_123"],
        "user_id": "platform_user_123",
        "session_id": "session_abc",
        "discoverable_handle": "test_user@gmail.com",
        "celebrations": [],
        "feedback_prompts": []
    }

# 2. TEST: Retrieval Node Logic
@pytest.mark.asyncio
async def test_retrieval_node_standardization(base_state):
    """
    Ensures tickers are standardized with .NS and invalid ones are filtered.
    """
    # Mock the db manager to prevent real network calls
    with patch("src.agents.retrieval_node.db") as mock_db:
        mock_db.connect = AsyncMock()
        mock_db.get_memory = AsyncMock(return_value=None)

        result = await retrieval_node(base_state)

        # Verify .NS addition
        assert "TCS.NS" in result["tickers"]
        assert "RELIANCE.NS" in result["tickers"]

        # Verify invalid ticker rejection
        assert "Invalid_Ticker_123" not in result["tickers"]
        assert len(result["feedback_prompts"]) > 0 # Should trigger rejection prompt

@pytest.mark.asyncio
async def test_retrieval_node_ltm_integration(base_state):
    """
    Ensures LTM stance is correctly retrieved from 'PostgreSQL' (Mocked).
    """
    past_memory = {
        "stance": "BULLISH",
        "logic_summary": "Historical support at 3200",
        "analysis_date": MagicMock()
    }
    past_memory['analysis_date'].isoformat.return_value = "2026-04-01T12:00:00"

    with patch("src.agents.retrieval_node.db") as mock_db:
        mock_db.connect = AsyncMock()
        mock_db.get_memory = AsyncMock(return_value=past_memory)

        result = await retrieval_node(base_state)

        assert "TCS.NS" in result["historical_stances"]
        assert result["historical_stances"]["TCS.NS"]["last_stance"] == "BULLISH"

@pytest.mark.asyncio
async def test_retrieval_celebration_trigger(base_state):
    """
    Ensures confetti is triggered for 5+ stocks.
    """
    base_state["tickers"] = ["TCS", "INFY", "RELIANCE", "WIPRO", "HDFC"]

    with patch("src.agents.retrieval_node.db") as mock_db:
        mock_db.connect = AsyncMock()
        mock_db.get_memory = AsyncMock(return_value=None)

        result = await retrieval_node(base_state)

        # Check for celebration
        celebration_types = [c["type"] for c in result["celebrations"]]
        assert "CONFETTI_LOW" in celebration_types
