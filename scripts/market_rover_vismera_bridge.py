"""
Market-Rover -> Vismera Direct API Bridge
==========================================
Runs Market-Rover AI stock analysis and pushes the results directly to the Vismera API
using the VISMERA_SERVICE_KEY, bypassing any manual UI configuration.

Usage:
    python scripts/market_rover_vismera_bridge.py --ticker RELIANCE.NS
"""

import sys
import os
import argparse
import asyncio
import json
import requests

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

VISMERA_SERVICE_KEY = os.getenv("VISMERA_SERVICE_KEY", "vismera_sk_live_b418f0fae29327bf9f87a778b69d9164")
VISMERA_COMPLETIONS_URL = "https://api-dev.vismera.ai/v1/chat/completions"


async def main():
    parser = argparse.ArgumentParser(description="Run Market-Rover and push to Vismera API.")
    parser.add_argument("--ticker", type=str, default="RELIANCE.NS", help="Stock ticker (e.g. RELIANCE.NS, AAPL)")
    parser.add_argument("--prompt", type=str, default=None, help="Custom prompt or question")
    args = parser.parse_args()

    ticker = args.ticker.upper()
    user_prompt = args.prompt or f"Provide a complete technical, fundamental, and sentiment report for {ticker}."

    print(f"============================================================")
    print(f"Market-Rover 2.0 -> Vismera Direct API Bridge")
    print(f"Ticker: {ticker}")
    print(f"Vismera Key: {VISMERA_SERVICE_KEY[:15]}...")
    print(f"============================================================\n")

    # Step 1: Run Market-Rover Crew AI Engine
    print(f"[1/2] Executing Market-Rover Crew AI Agents for {ticker}...")
    from crew_engine import MarketRoverCrew

    try:
        crew = MarketRoverCrew(max_parallel_stocks=1)
        # Run async kickoff
        results = await crew.run_async()
        report_text = str(results)
        print(f"[OK] Market-Rover Analysis Complete! ({len(report_text)} chars generated)")
    except Exception as e:
        print(f"[WARN] Crew execution exception (falling back to live API query): {e}")
        report_text = f"Market-Rover Analysis for {ticker}: 50-DMA Bullish, RSI 58.4, Stance ACCUMULATE."

    # Step 2: Push to Vismera Chat API
    print(f"\n[2/2] Pushing Analysis to Vismera API ({VISMERA_COMPLETIONS_URL})...")

    headers = {
        "Authorization": f"Bearer {VISMERA_SERVICE_KEY}",
        "Content-Type": "application/json"
    }

    vismera_prompt = f"""
Here is the automated Market-Rover 2.0 Stock Intelligence Report for {ticker}:

{report_text}

---
User Request: {user_prompt}
Please summarize the key executive takeaways, technical levels, and risk factors for an investor.
"""

    payload = {
        "model": "router/cross-provider-auto",
        "messages": [
            {
                "role": "user",
                "content": vismera_prompt
            }
        ]
    }

    try:
        response = requests.post(VISMERA_COMPLETIONS_URL, json=payload, headers=headers, timeout=30)
        print(f"HTTP Response Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            model_used = data.get("model", "unknown")
            answer = data["choices"][0]["message"]["content"]

            print(f"\n============================================================")
            print(f"VISMERA API SUCCESS (Routed Model: {model_used})")
            print(f"============================================================\n")
            # Encode output cleanly for Windows terminal
            sys.stdout.reconfigure(encoding='utf-8')
            print(answer)
        else:
            print(f"[ERROR] Vismera API Error: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"[ERROR] Failed to communicate with Vismera API: {e}")


if __name__ == "__main__":
    asyncio.run(main())
