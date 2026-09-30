#!/usr/bin/env python3
"""
scripts/verify_frontend_health.py

Green-on-Arrival (GoA) Deep Frontend & Asset Integrity Health Checker.
Validates that:
1. All 4 frontend SPAs (/, /hil, /investbrand, /pledge) serve valid HTML containing the root DOM mount.
2. Every JavaScript bundle and CSS stylesheet referenced in index.html exists, loads with 200 OK, and is NOT a fallback HTML.
3. Client-side deep link routes fallback properly to index.html without 404 or MIME error.
4. Non-existent static assets return 404 JSON (preventing browser script MIME type syntax errors).
5. All backend API routes remain isolated from frontend SPA fallbacks.
"""
import sys
import re
from pathlib import Path
from starlette.testclient import TestClient

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from server import app

client = TestClient(app)

FRONTEND_TARGETS = [
    {
        "name": "Market Rover Core",
        "route": "/",
        "deep_link": "/screener",
        "static_dir": REPO_ROOT / "static" / "market_rover",
    },
    {
        "name": "HIL Mission Control",
        "route": "/hil",
        "deep_link": "/hil/governance",
        "static_dir": REPO_ROOT / "static" / "hil_rover",
    },
    {
        "name": "InvestBrand",
        "route": "/investbrand",
        "deep_link": "/investbrand/explore",
        "static_dir": REPO_ROOT / "static" / "investbrand",
    },
    {
        "name": "Pledge Rover",
        "route": "/pledge",
        "deep_link": "/pledge/promoter/RELIANCE",
        "static_dir": REPO_ROOT / "static" / "pledge_rover",
    },
]

def extract_asset_urls(html_text: str):
    """Extracts script src and link stylesheet href URLs from index.html."""
    scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html_text, re.IGNORECASE)
    styles = re.findall(r'<link[^>]+rel=["\']stylesheet["\'][^>]+href=["\']([^"\']+)["\']', html_text, re.IGNORECASE)
    styles_alt = re.findall(r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']stylesheet["\']', html_text, re.IGNORECASE)
    return list(set(scripts + styles + styles_alt))

def run_health_checks():
    print("=" * 65)
    print(" MARKET-ROVER GOA FRONTEND & ASSET INTEGRITY AUDIT")
    print("=" * 65)

    all_passed = True
    total_assets_checked = 0

    # 1. Test each SPA route
    for target in FRONTEND_TARGETS:
        name = target["name"]
        route = target["route"]
        deep_link = target["deep_link"]

        print(f"\n[SPA] Testing {name} ({route})...")

        # A. Fetch index HTML
        res = client.get(route)
        if res.status_code != 200:
            print(f"  [FAIL] {route} returned HTTP {res.status_code}")
            all_passed = False
            continue

        html = res.text
        if "<div id=\"root\"" not in html and "<div id='root'" not in html and "id=\"root\"" not in html:
            print(f"  [FAIL] {route} HTML is missing React DOM root (<div id=\"root\">)")
            all_passed = False
        else:
            print(f"  [PASS] Root DOM Element: Found (<div id=\"root\"> present)")

        # B. Check deep link client-side fallback
        deep_res = client.get(deep_link)
        if deep_res.status_code != 200 or "id=\"root\"" not in deep_res.text:
            print(f"  [FAIL] Deep link {deep_link} failed client-side fallback (HTTP {deep_res.status_code})")
            all_passed = False
        else:
            print(f"  [PASS] Client Deep-Link: {deep_link} resolved successfully (HTTP 200)")

        # C. Extract and test each referenced static asset
        assets = extract_asset_urls(html)
        print(f"  [INFO] Referenced JS/CSS Assets: {len(assets)} found")

        for asset_url in assets:
            total_assets_checked += 1
            # Normalize asset URL
            fetch_url = asset_url if asset_url.startswith("/") else f"/{asset_url}"
            asset_res = client.get(fetch_url)

            if asset_res.status_code != 200:
                print(f"    [FAIL] Asset: {fetch_url} -> HTTP {asset_res.status_code}")
                all_passed = False
            elif "<!doctype html" in asset_res.text.lower() or "<html" in asset_res.text.lower():
                print(f"    [FAIL] Asset MIME Glitch: {fetch_url} returned HTML fallback instead of real asset!")
                all_passed = False
            elif len(asset_res.content) == 0:
                print(f"    [FAIL] Asset: {fetch_url} is empty (0 bytes)!")
                all_passed = False
            else:
                size_kb = len(asset_res.content) / 1024
                print(f"    [PASS] Asset OK: {fetch_url} ({size_kb:.1f} KB, HTTP 200)")

    # 2. Test MIME Guard & 404 Safety
    print("\n[GUARD] Testing Static Asset 404 MIME-Guard...")
    missing_asset = client.get("/assets/non_existent_bundle_12345.js")
    if missing_asset.status_code == 404 and missing_asset.headers.get("content-type", "").startswith("application/json"):
        print("  [PASS] Missing .js asset returns HTTP 404 JSON (prevents HTML script MIME crash)")
    else:
        print(f"  [FAIL] Missing .js asset returned HTTP {missing_asset.status_code} with content-type {missing_asset.headers.get('content-type')}")
        all_passed = False

    # 3. Test API Isolation
    print("\n[API] Testing API Gateway Isolation...")
    api_health = client.get("/api/v1/health")
    if api_health.status_code == 200 and "services" in api_health.json():
        print(f"  [PASS] /api/v1/health operational -> {api_health.json().get('services')}")
    else:
        print(f"  [FAIL] /api/v1/health returned {api_health.status_code}")
        all_passed = False

    print("\n" + "=" * 65)
    if all_passed:
        print(f" [SUCCESS] ALL {len(FRONTEND_TARGETS)} SPAS & {total_assets_checked} ASSETS VERIFIED HEALTHY!")
        print("=" * 65)
        sys.exit(0)
    else:
        print(" [FAILURE] Frontend integrity check failed!")
        print("=" * 65)
        sys.exit(1)

if __name__ == "__main__":
    run_health_checks()
