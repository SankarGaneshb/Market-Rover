"""
test_pledge_rover_comprehensive.py — Comprehensive Unit Test Suite for Pledge Rover Backend.
Covers:
  - pledge_rover/backend/src/data/scoring.py
  - pledge_rover/backend/src/data/mock_historical.py
  - pledge_rover/backend/src/data/scan_manager.py
  - pledge_rover/backend/src/routes/health.py
  - pledge_rover/backend/src/routes/promoters.py
  - pledge_rover/backend/src/routes/pledges.py
  - pledge_rover/backend/src/routes/agents.py
  - pledge_rover/backend/src/agents/harvester.py
  - pledge_rover/backend/src/agents/council.py
  - pledge_rover/backend/src/agents/sre_agent.py
  - pledge_rover/backend/src/utils/ops_support.py
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from pledge_rover.backend.src.data.scoring import (
    calculate_skin_in_the_game,
    survival_score,
)
from pledge_rover.backend.src.data.mock_historical import (
    get_enriched_promoter_data,
    get_all_enriched_promoters,
    MOCK_HISTORICAL_DATA
)
from pledge_rover.backend.src.data.scan_manager import ScanManager
from pledge_rover.backend.src.routes import api_router as pledge_router
from pledge_rover.backend.src.routes.pledges import sync_promoters_to_db
from pledge_rover.backend.src.routes.agents import perform_scan_background
from pledge_rover.backend.src.agents.harvester import ExchangeHarvester
from pledge_rover.backend.src.agents.council import create_council_crew, run_council
from pledge_rover.backend.src.agents.sre_agent import SRESentinel
from pledge_rover.backend.src.utils.ops_support import analyze_error_async

# Create test app with pledge router
app = FastAPI()
app.include_router(pledge_router, prefix="/api/v1/pledge")
client = TestClient(app)


# ── Helper for async_session Mocking ──────────────────────────────────────────

def _make_mock_session_cm(session_mock):
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=session_mock)
    cm.__aexit__ = AsyncMock(return_value=None)
    return cm


# ── 1. Scoring & Mathematical Framework Tests ─────────────────────────────────

def test_skin_in_the_game_normal_promoter():
    res = calculate_skin_in_the_game(promoter_holding_pct=60.0, pledged_pct=12.0)
    assert res["type"] == "Promoter Controlled"
    assert res["layer1_commitment"] == 80.0
    assert res["layer2_concentration"] == 0.8
    assert res["final_skin_pct"] == 64.0


def test_skin_in_the_game_zero_promoter():
    res = calculate_skin_in_the_game(
        promoter_holding_pct=0.0,
        pledged_pct=0.0,
        is_zero_promoter=True,
        insider_nee_pct=8.5
    )
    assert res["type"] == "Professionally Managed Entity"
    assert res["final_skin_pct"] == 8.5
    assert "Zero-promoter" in res["description"]


def test_skin_in_the_game_psu_and_zero_holding():
    # PSU holding > 75%
    res_psu = calculate_skin_in_the_game(promoter_holding_pct=85.0, pledged_pct=0.0, is_psu=True)
    assert res_psu["type"] == "PSU"
    assert res_psu["final_skin_pct"] == 100.0

    # Negative / zero ceiling
    res_zero = calculate_skin_in_the_game(promoter_holding_pct=-5.0, pledged_pct=0.0)
    assert res_zero["final_skin_pct"] == 0.0


def test_survival_score_all_patterns():
    # Growth Pattern (low velocity, positive corr, Tier 1, positive OCF)
    growth_data = {
        "pledge_qoq_change": 0.0,
        "price_pledge_pearson_8q": 0.5,
        "pledgee_tier": "Tier1Bank",
        "ocf_trend": "positive",
        "pledge_std_dev_8q": 0.5,
        "release_create_ratio": 1.5
    }
    g_res = survival_score(growth_data)
    assert g_res["intent_label"] == "Growth"
    assert g_res["trust_signal"] == "Positive"

    # Survival Pattern (high velocity, inverse corr, RelatedParty, negative OCF)
    survival_data = {
        "pledge_qoq_change": 6.0,
        "price_pledge_pearson_8q": -0.8,
        "pledgee_tier": "RelatedParty",
        "ocf_trend": "negative",
        "pledge_std_dev_8q": 5.0,
        "release_create_ratio": 0.2
    }
    s_res = survival_score(survival_data)
    assert s_res["intent_label"] == "Survival"
    assert s_res["trust_signal"] == "Warning"

    # Uncertain Pattern (NBFC, flat OCF)
    uncertain_data = {
        "pledge_qoq_change": 3.0,
        "price_pledge_pearson_8q": -0.2,
        "pledgee_tier": "NBFC",
        "ocf_trend": "flat",
        "pledge_std_dev_8q": 2.0,
        "release_create_ratio": 1.0
    }
    u_res = survival_score(uncertain_data)
    assert u_res["intent_label"] == "Uncertain"
    assert u_res["trust_signal"] == "Neutral"


# ── 2. Mock Historical Enrichment Tests ────────────────────────────────────────

def test_mock_historical_enrichment():
    enriched = get_enriched_promoter_data("LLOYDSME")
    assert enriched is not None
    assert enriched["symbol"] == "LLOYDSME"
    assert enriched["skin_in_the_game"] > 0
    assert enriched["survival_score"] >= 0

    assert get_enriched_promoter_data("NONEXISTENT") is None

    all_promoters = get_all_enriched_promoters()
    assert len(all_promoters) == len(MOCK_HISTORICAL_DATA)


# ── 3. ScanManager State Tests ────────────────────────────────────────────────

def test_scan_manager_state():
    ScanManager.set_status("scanning", "Active test scan...")
    assert ScanManager.is_scanning() is True
    state = ScanManager.get_state()
    assert state["status"] == "scanning"
    assert "Active test scan" in state["message"]

    ScanManager.set_status("idle", "Scan done.")
    assert ScanManager.is_scanning() is False


# ── 4. Routes Tests ───────────────────────────────────────────────────────────

def test_pledge_rover_health_endpoint():
    res = client.get("/api/v1/pledge/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "Pledge Rover API"
    assert "timestamp" in data


def test_pledge_rover_promoter_endpoints():
    class FakePromoter:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    promoter_obj = FakePromoter(
        symbol="LLOYDSME",
        company_name="Lloyds Metals",
        governance_score=3.5,
        total_shares=500.0,
        holding_pct=65.0,
        pledged_pct=30.0,
        skin_in_the_game=50.0,
        skin_layer1=60.0,
        skin_layer2=0.8,
        survival_score=65.0,
        intent_label="Survival",
        trust_signal="Warning",
        release_create_ratio=0.5,
        risk="High"
    )

    mock_scalars = MagicMock()
    mock_scalars.first.return_value = promoter_obj
    mock_scalars.all.return_value = [promoter_obj]
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    with patch("pledge_rover.backend.src.routes.promoters.async_session", return_value=_make_mock_session_cm(mock_session)):
        # Get Single Promoter
        res = client.get("/api/v1/pledge/promoters/LLOYDSME")
        assert res.status_code == 200
        assert res.json()["symbol"] == "LLOYDSME"

        # Low risk branch
        promoter_obj.pledged_pct = 2.0
        promoter_obj.governance_score = 8.5
        res_low = client.get("/api/v1/pledge/promoters/LLOYDSME")
        assert res_low.status_code == 200
        assert res_low.json()["risk"] == "Low"

        # Medium risk branch
        promoter_obj.pledged_pct = 15.0
        promoter_obj.governance_score = 5.5
        res_med = client.get("/api/v1/pledge/promoters/LLOYDSME")
        assert res_med.status_code == 200
        assert res_med.json()["risk"] == "Medium"

        # List Promoters
        res_list = client.get("/api/v1/pledge/promoters/")
        assert res_list.status_code == 200
        assert len(res_list.json()) == 1


def test_pledge_rover_promoter_not_found():
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = None
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    with patch("pledge_rover.backend.src.routes.promoters.async_session", return_value=_make_mock_session_cm(mock_session)):
        res = client.get("/api/v1/pledge/promoters/UNKNOWN")
        assert res.status_code == 404
        assert res.json()["detail"] == "Promoter not found"


def test_pledge_rover_pledges_feed():
    mock_feed = [
        {
            "symbol": "LLOYDSME",
            "company_name": "Lloyds Metals",
            "percentage_pledged": 12.0,
            "ltv_ratio": 1.6,
            "purpose": "Working capital"
        },
        {
            "symbol": "NOCIL",
            "company_name": "NOCIL Ltd",
            "percentage_pledged": 2.0,
            "ltv_ratio": 0.8,
            "purpose": "Capex"
        }
    ]
    with patch.object(ExchangeHarvester, "get_7_day_combined_feed", new_callable=AsyncMock) as mock_harv, \
         patch("pledge_rover.backend.src.routes.pledges.sync_promoters_to_db", new_callable=AsyncMock):
        mock_harv.return_value = mock_feed

        res = client.get("/api/v1/pledge/pledges/feed")
        assert res.status_code == 200
        data = res.json()
        assert "metrics" in data
        assert data["metrics"]["active_contagions"] == 1
        assert data["metrics"]["promoters_tracked"] == 2
        assert len(data["events"]) == 2


@pytest.mark.asyncio
async def test_sync_promoters_to_db():
    events = [
        {"symbol": "NEW_SYM", "company_name": "New Corp", "percentage_pledged": 10.0},
        {"symbol": "EXISTING_SYM", "percentage_pledged": 15.0}
    ]

    existing_promoter = MagicMock()
    existing_promoter.pledged_pct = 5.0

    mock_scalars_new = MagicMock()
    mock_scalars_new.first.return_value = None
    mock_result_new = MagicMock()
    mock_result_new.scalars.return_value = mock_scalars_new

    mock_scalars_exist = MagicMock()
    mock_scalars_exist.first.return_value = existing_promoter
    mock_result_exist = MagicMock()
    mock_result_exist.scalars.return_value = mock_scalars_exist

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(side_effect=[mock_result_new, mock_result_exist])
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.begin = MagicMock(return_value=_make_mock_session_cm(mock_session))

    with patch("pledge_rover.backend.src.routes.pledges.async_session", return_value=_make_mock_session_cm(mock_session)):
        await sync_promoters_to_db(events)
        assert mock_session.add.called
        assert existing_promoter.pledged_pct == 15.0


def test_pledge_rover_agents_trigger_and_status():
    with patch.object(ScanManager, "is_scanning", return_value=False), \
         patch("pledge_rover.backend.src.routes.agents.perform_scan_background", new_callable=AsyncMock):
        res = client.post("/api/v1/pledge/agents/trigger", json={"filing_text": "Sample filing text"})
        assert res.status_code == 200
        assert res.json()["status"] == "scanning"

        # When already scanning
        with patch.object(ScanManager, "is_scanning", return_value=True):
            res_busy = client.post("/api/v1/pledge/agents/trigger", json={})
            assert res_busy.status_code == 200
            assert "already in progress" in res_busy.json()["message"]

        # Status check
        status_res = client.get("/api/v1/pledge/agents/status")
        assert status_res.status_code == 200


@pytest.mark.asyncio
async def test_perform_scan_background_workflow():
    mock_promoter = MagicMock()
    mock_promoter.id = 1
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = mock_promoter
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.flush = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.begin = MagicMock(return_value=_make_mock_session_cm(mock_session))

    with patch("pledge_rover.backend.src.routes.agents.run_council", new_callable=AsyncMock) as mock_council, \
         patch("pledge_rover.backend.src.config.database.async_session", return_value=_make_mock_session_cm(mock_session)):
        mock_council.return_value = {
            "governance_score": 6.5,
            "final_sentiment": "Growth",
            "debate_summary": "Solid rationale"
        }

        await perform_scan_background("Explicit Filing Text")
        assert mock_promoter.governance_score == 6.5


# ── 5. Agents & Harvester Tests ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_exchange_harvester_bse_nse_fallback():
    harvester = ExchangeHarvester()

    # Test BSE fetch fallback on network error
    with patch("httpx.AsyncClient.get", side_effect=Exception("Connection refused")):
        bse_res = await harvester.fetch_bse_recent_pledges()
        assert len(bse_res) > 0
        assert bse_res[0]["exchange"] == "BSE"

        nse_res = await harvester.fetch_nse_recent_pledges()
        assert len(nse_res) > 0
        assert nse_res[0]["exchange"] == "NSE"

    # Test Combined 7-day feed
    with patch.object(harvester, "fetch_bse_recent_pledges", new_callable=AsyncMock) as mock_bse, \
         patch.object(harvester, "fetch_nse_recent_pledges", new_callable=AsyncMock) as mock_nse:
        mock_bse.return_value = [{"symbol": "BSE_SYM", "percentage_pledged": 5.0, "date": "2026-09-20"}]
        mock_nse.return_value = [{"symbol": "NSE_SYM", "percentage_pledged": 8.0, "date": "2026-09-21"}]

        combined = await harvester.get_7_day_combined_feed()
        assert len(combined) == 2


def test_council_crew_initialization():
    with patch("pledge_rover.backend.src.agents.council.Agent") as mock_agent, \
         patch("pledge_rover.backend.src.agents.council.Task") as mock_task, \
         patch("pledge_rover.backend.src.agents.council.Crew") as mock_crew, \
         patch("pledge_rover.backend.src.agents.council.ChatGoogleGenerativeAI"):
        mock_crew_instance = MagicMock()
        mock_crew.return_value = mock_crew_instance
        crew = create_council_crew("Filing Text", {"skin_in_the_game": 50, "survival_score": 40})
        assert crew == mock_crew_instance
        assert mock_agent.call_count == 4
        assert mock_task.call_count == 4


@pytest.mark.asyncio
async def test_run_council_execution():
    with patch("pledge_rover.backend.src.agents.council.create_council_crew") as mock_create:
        mock_crew = MagicMock()
        mock_crew.kickoff.return_value = {
            "promoter_symbol": "TEST",
            "governance_score": 7.5,
            "final_sentiment": "Growth"
        }
        mock_create.return_value = mock_crew

        res = await run_council("Test Filing")
        assert res["governance_score"] == 7.5


def test_sre_sentinel():
    sentinel = SRESentinel(agent_name="Test-SRE")
    with patch("pledge_rover.backend.src.agents.sre_agent.notify_hil") as mock_hil:
        mock_hil.return_value = {"status": "dispatched"}
        res = sentinel.report_failure("Task1", "DB Failure", severity="CRITICAL")
        assert res["status"] == "dispatched"
        mock_hil.assert_called_once()

    assert sentinel.verify_voter_api_health() is True


@pytest.mark.asyncio
async def test_ops_support_diagnostic():
    # No API key case
    with patch.dict("os.environ", {}, clear=True):
        res_none = await analyze_error_async(Exception("Boom"), context="testing")
        assert res_none is None

    # Success case with API key
    with patch.dict("os.environ", {"GOOGLE_API_KEY": "fake_key"}), \
         patch("google.generativeai.GenerativeModel") as mock_model, \
         patch("anyio.to_thread.run_sync") as mock_sync:
        mock_resp = MagicMock()
        mock_resp.text = '{"rootCause": "Timeout on upstream API", "severity": "low"}'
        mock_sync.return_value = mock_resp

        res = await analyze_error_async(Exception("Timeout Error"), context="harvester")
        assert res is not None
        assert "rootCause" in res
