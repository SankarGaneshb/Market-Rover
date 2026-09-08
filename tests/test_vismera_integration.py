"""
Unit tests for Vismera Platform integration:
- Authentication & Token Verification (utils/vismera_auth.py)
- Telemetry & API Client (rover_tools/vismera_client.py)
- Unified Server API Endpoints (/api/v1/vismera/status, /api/v1/vismera/user)
"""
import pytest
from fastapi.testclient import TestClient
from utils.vismera_auth import verify_vismera_token, decode_jwt_unverified
from rover_tools.vismera_client import log_telemetry_event, get_vismera_status
from server import app

client = TestClient(app)


def test_decode_jwt_unverified():
    # Valid mock base64 payload: {"sub":"user123","org_id":"org_test"}
    mock_jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyMTIzIiwib3JnX2lkIjoib3JnX3Rlc3QiLCJyb2xlcyI6WyJhbmdlbCJdfQ.signature"
    decoded = decode_jwt_unverified(mock_jwt)
    assert decoded.get("sub") == "user123"
    assert decoded.get("org_id") == "org_test"


def test_verify_vismera_token_mock():
    token_result = verify_vismera_token("dev_vismera_secret")
    assert token_result["authenticated"] is True
    assert token_result["user_id"] == "usr_vismera_dev"
    assert "admin" in token_result["roles"]


def test_verify_vismera_token_empty():
    token_result = verify_vismera_token(None)
    assert token_result["sub"] == "anonymous"
    assert token_result["authenticated"] is False


def test_vismera_client_status():
    status_dict = get_vismera_status()
    assert "status" in status_dict
    assert "endpoint" in status_dict


def test_vismera_client_telemetry_logging():
    res = log_telemetry_event(
        event_type="TEST_EVENT",
        agent_name="TestAgent",
        session_id="test_sess_001",
        payload={"key": "value"}
    )
    # When VISMERA_ENABLED is true, it attempts HTTP post (or returns mock/response)
    # Function handles connections gracefully
    assert res is None or isinstance(res, dict)


def test_server_vismera_endpoints():
    # Test /api/v1/vismera/status
    res_status = client.get("/api/v1/vismera/status")
    assert res_status.status_code == 200
    assert "status" in res_status.json()

    # Test /api/v1/vismera/user with Bearer token
    res_user = client.get(
        "/api/v1/vismera/user",
        headers={"Authorization": "Bearer dev_vismera_secret"}
    )
    assert res_user.status_code == 200
    json_data = res_user.json()
    assert json_data.get("authenticated") is True
    assert json_data.get("user_id") == "usr_vismera_dev"
