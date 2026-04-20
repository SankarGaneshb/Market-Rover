"""
test_phase3_routes.py — Tests for Phase 3 route modules.

Routes calendar, heatmap, shadow are in src/routes/ but NOT mounted in server.py.
We create a minimal test app that includes the router to test them in isolation.
All external I/O (DB, yfinance) is mocked.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Build a minimal test app with the full routes package mounted
from src.routes import router as api_router

_test_app = FastAPI()
_test_app.include_router(api_router, prefix="/api")
route_client = TestClient(_test_app)

# Also use the main server client for server-level route tests
from src.server import app
server_client = TestClient(app)


# ── Calendar Routes (src/routes/calendar.py) ────────────────────────────────

def test_calendar_muhurtham_2026():
    res = route_client.get("/api/calendar/muhurtham/2026")
    assert res.status_code == 200
    data = res.json()
    assert data["year"] == 2026
    assert len(data["windows"]) > 0
    names = [w["name"] for w in data["windows"]]
    assert "Akshaya Tritiya" in names


def test_calendar_seasonal():
    res = route_client.get("/api/calendar/seasonal")
    assert res.status_code == 200
    data = res.json()
    assert "patterns" in data
    assert len(data["patterns"]) >= 4
    seasons = [p["season"] for p in data["patterns"]]
    assert "Budget Rally" in seasons
    assert "Festive Rally" in seasons


# ── Profile Analyze via route_client ────────────────────────────────────────

def test_profile_analyze_preserver():
    res = route_client.post("/api/profile/analyze", json={"q1": 1, "q2": 1, "q3": 1})
    assert res.status_code == 200
    assert res.json()["persona"] == "The Preserver"
    assert res.json()["score"] == 3


def test_profile_analyze_hunter():
    res = route_client.post("/api/profile/analyze", json={"q1": 3, "q2": 3, "q3": 3})
    assert res.status_code == 200
    assert res.json()["persona"] == "The Hunter"
    assert res.json()["score"] == 9


def test_profile_analyze_defender():
    res = route_client.post("/api/profile/analyze", json={"q1": 2, "q2": 2, "q3": 2})
    assert res.status_code == 200
    assert res.json()["persona"] == "The Defender"


def test_profile_analyze_compounder():
    res = route_client.post("/api/profile/analyze", json={"q1": 3, "q2": 2, "q3": 2})
    assert res.status_code == 200
    assert res.json()["persona"] == "The Compounder"


# ── Shadow Routes (src/routes/shadow.py) ────────────────────────────────────

@pytest.mark.asyncio
async def test_shadow_user_returns_list():
    mock_row = {
        "ticker": "TCS.NS",
        "stance": "ACCUMULATION",
        "logic_summary": "Institutional absorption confirmed.",
        "analysis_date": MagicMock()
    }
    mock_row["analysis_date"].isoformat.return_value = "2026-04-15T10:00:00"

    with patch("src.routes.shadow.db") as mock_db:
        mock_db.connect = AsyncMock()
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[mock_row])
        mock_pool.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.__aexit__ = AsyncMock(return_value=None)
        mock_db.pool = MagicMock()
        mock_db.pool.acquire = MagicMock(return_value=mock_pool)

        res = route_client.get("/api/shadow/test@gmail.com")
        assert res.status_code == 200


# ── Heatmap Route (src/routes/heatmap.py) ────────────────────────────────────

def test_heatmap_no_data_returns_404():
    with patch("src.routes.heatmap.yf.download") as mock_dl:
        import pandas as pd
        mock_dl.return_value = pd.DataFrame()
        res = route_client.get("/api/heatmap/FAKEXXX")
        assert res.status_code == 404


def test_heatmap_valid_ticker():
    with patch("src.routes.heatmap.yf.download") as mock_dl:
        import pandas as pd
        from datetime import datetime
        idx = pd.DatetimeIndex([
            datetime(2024, 1, 31), datetime(2024, 2, 29),
            datetime(2024, 3, 31), datetime(2024, 4, 30),
        ])
        mock_dl.return_value = pd.DataFrame(
            {"Close": [100.0, 103.5, 101.2, 107.8]},
            index=idx
        )
        res = route_client.get("/api/heatmap/TCS")
        assert res.status_code == 200
        data = res.json()
        assert data["ticker"] == "TCS.NS"
        assert "data" in data
        assert "best" in data
        assert "worst" in data
