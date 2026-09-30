"""
tests/test_frontend_integrity.py

Automated Pytest Suite for Green-on-Arrival (GoA) Frontend & Asset Integrity.
Verifies:
1. Root DOM element presence in all 4 SPAs.
2. Resolution and non-empty content for all referenced JS/CSS asset files.
3. Client-side routing fallback for deep link paths.
4. Static asset 404 MIME guard.
5. API gateway health check isolation.
"""
import pytest
import re
from starlette.testclient import TestClient
from server import app

client = TestClient(app)

SPAS = [
    ("/", "/screener"),
    ("/hil", "/hil/governance"),
    ("/investbrand", "/investbrand/explore"),
    ("/pledge", "/pledge/promoter/RELIANCE"),
]

def extract_asset_urls(html_text: str):
    scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html_text, re.IGNORECASE)
    styles = re.findall(r'<link[^>]+rel=["\']stylesheet["\'][^>]+href=["\']([^"\']+)["\']', html_text, re.IGNORECASE)
    styles_alt = re.findall(r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']stylesheet["\']', html_text, re.IGNORECASE)
    return list(set(scripts + styles + styles_alt))

@pytest.mark.parametrize("route,deep_link", SPAS)
def test_spa_root_and_deep_link_resolution(route, deep_link):
    # 1. Main Route
    res = client.get(route)
    assert res.status_code == 200, f"Route {route} failed with HTTP {res.status_code}"
    assert 'id="root"' in res.text or "id='root'" in res.text, f"Route {route} missing React root DOM mount"

    # 2. Deep Link Route
    deep_res = client.get(deep_link)
    assert deep_res.status_code == 200, f"Deep link {deep_link} failed with HTTP {deep_res.status_code}"
    assert 'id="root"' in deep_res.text or "id='root'" in deep_res.text, f"Deep link {deep_link} missing React root DOM mount"

    # 3. Referenced Static Assets
    assets = extract_asset_urls(res.text)
    assert len(assets) > 0, f"No static JS/CSS assets referenced in {route} HTML"

    for asset_url in assets:
        fetch_url = asset_url if asset_url.startswith("/") else f"/{asset_url}"
        asset_res = client.get(fetch_url)
        assert asset_res.status_code == 200, f"Asset {fetch_url} in {route} returned HTTP {asset_res.status_code}"
        assert "<!doctype html" not in asset_res.text.lower(), f"Asset {fetch_url} returned fallback HTML instead of static file"
        assert len(asset_res.content) > 0, f"Asset {fetch_url} is empty (0 bytes)"

def test_static_asset_mime_guard():
    res = client.get("/assets/non_existent_bundle_99999.js")
    assert res.status_code == 404
    assert res.headers.get("content-type", "").startswith("application/json")

def test_api_gateway_health():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data.get("status") == "healthy"
    assert "services" in data
