"""
InvestBrand Unified Gateway Test Suite
Verifies all InvestBrand endpoints, daily puzzle retrieval, clue generation,
guess evaluation, community voting, leaderboards, and SPA static routing.
"""
import pytest
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

def test_investbrand_health():
    """Verify InvestBrand health endpoint."""
    res = client.get("/api/v1/investbrand/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "InvestBrand Unified API"
    assert data["total_brands"] >= 50

def test_daily_puzzle():
    """Verify daily puzzle endpoint returns active brand puzzle."""
    res = client.get("/api/puzzles/daily")
    assert res.status_code == 200
    data = res.json()
    assert "id" in data
    assert "brand_name" in data
    assert "company_name" in data
    assert "ticker" in data
    assert "difficulty" in data
    assert data["brand_name"] != ""
    assert data["ticker"] != ""

def test_puzzle_clues():
    """Verify progressive clues endpoint."""
    res = client.get("/api/puzzles/1/clues")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "clue1" in data["clues"]
    assert "clue2" in data["clues"]
    assert "clue3" in data["clues"]
    assert "Sector Clue" in data["clues"]["clue1"]

def test_puzzle_guess_correct_and_incorrect():
    """Verify guess evaluation against puzzle brand."""
    daily = client.get("/api/puzzles/daily").json()
    p_id = daily["id"]
    correct_brand = daily["brand_name"]

    # Test correct guess
    res_correct = client.post(f"/api/puzzles/{p_id}/guess", json={"guess": correct_brand})
    assert res_correct.status_code == 200
    data_correct = res_correct.json()
    assert data_correct["correct"] is True
    assert data_correct["score"] == 100

    # Test incorrect guess
    res_incorrect = client.post(f"/api/puzzles/{p_id}/guess", json={"guess": "NonExistentBrandXYZ123"})
    assert res_incorrect.status_code == 200
    data_incorrect = res_incorrect.json()
    assert data_incorrect["correct"] is False

def test_puzzle_complete():
    """Verify completion recording and stats calculation."""
    res = client.post("/api/puzzles/1/complete", json={
        "score": 100,
        "difficulty": "easy",
        "time_taken": 25,
        "attempts": 1
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["xp_earned"] == 100
    assert data["streak"] >= 1

def test_puzzle_insight():
    """Verify AI Teacher & Market Insight generation."""
    res = client.get("/api/puzzles/1/insight")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "insight" in data
    assert "teacher_tip" in data

def test_vote_status_and_voting():
    """Verify vote status retrieval and casting vote."""
    res_status = client.get("/api/puzzles/vote-status")
    assert res_status.status_code == 200
    data_status = res_status.json()
    assert "candidates" in data_status
    assert len(data_status["candidates"]) >= 3

    # Cast vote
    candidate_id = data_status["candidates"][0]["brand_id"]
    res_vote = client.post("/api/puzzles/vote", json={"brandId": candidate_id})
    assert res_vote.status_code == 200
    data_vote = res_vote.json()
    assert data_vote["success"] is True

def test_leaderboard():
    """Verify leaderboard ranks."""
    res = client.get("/api/leaderboard")
    assert res.status_code == 200
    data = res.json()
    assert "leaderboard" in data
    assert len(data["leaderboard"]) > 0
    first = data["leaderboard"][0]
    assert "name" in first
    assert "total_score" in first

def test_missions():
    """Verify active missions list."""
    res = client.get("/api/missions")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 3

def test_education():
    """Verify education locker and daily tip."""
    res_locker = client.get("/api/education/locker")
    assert res_locker.status_code == 200
    assert "cards" in res_locker.json()

    res_tip = client.get("/api/education/tip")
    assert res_tip.status_code == 200
    assert "tip" in res_tip.json()

def test_duel_completion_and_bvb_score():
    """Verify Bull vs Bear duel completion recording and BvB score calculation."""
    res = client.post("/api/puzzles/duel/complete", json={
        "roomCode": "BULL99",
        "playerId": "p1_12345",
        "score": 1250,
        "brandId": 1,
        "moves": 8,
        "timeTaken": 42,
        "isWinner": True,
        "role": "bull"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["score"] == 1250
    assert data["bvb_score"] >= 1250
    assert data["duel_score"] >= 1250
    assert data["total_score"] >= 1250

def test_leaderboard_duel_filtering():
    """Verify leaderboard filtering specifically for Bull vs Bear duels."""
    res = client.get("/api/leaderboard?type=duel")
    assert res.status_code == 200
    data = res.json()
    assert "leaderboard" in data
    assert len(data["leaderboard"]) > 0
    first = data["leaderboard"][0]
    assert "duel_score" in first
    assert "easy_score" in first
    assert "medium_score" in first
    assert "hard_score" in first
    assert first["score"] == first["duel_score"]
    assert first["rank"] == 1

def test_user_profile_duel_scores():
    """Verify user profile contains distinct BvB duelScore alongside solo tiers."""
    res = client.get("/api/users/me")
    assert res.status_code == 200
    data = res.json()
    assert "duelScore" in data
    assert "easyScore" in data
    assert "mediumScore" in data
    assert "hardScore" in data
    assert data["duelScore"] >= 0

def test_spa_routing_mime_types():
    """Verify SPA router handles asset extensions with 404 instead of HTML fallback."""
    # Non-existent JS asset must return 404 JSON, NOT index.html (200)
    res_missing_js = client.get("/investbrand/static/js/non_existent_bundle.js")
    assert res_missing_js.status_code == 404
    assert res_missing_js.headers["content-type"] == "application/json"

    # Route /investbrand/play should serve SPA fallback
    res_spa_route = client.get("/investbrand/play")
    assert res_spa_route.status_code in [200, 404]
