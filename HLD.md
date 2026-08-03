# 🚀 Market-Rover System Design – High Level Design (HLD)

This document presents the **High Level Design (HLD) System Architecture** for **Market-Rover**, an AI-powered stock intelligence and portfolio research platform built for the Indian equity markets (Nifty, Sensex, Sector Indices, and Option Chains).

---

## 📊 High-Level Design (HLD) Diagram

![Market-Rover High Level Design Architecture](assets/market_rover_hld.png)

---

## 🏗️ Architectural Component Breakdown

### 1. User Layer (Ingestion & Entry Points)
* **User Interfaces**:
  * **Streamlit UI (`app.py`)**: Interactive web dashboard for portfolio uploads and live report viewing.
  * **React 19 Frontend**: Decoupled v5 SPA UI built with Vite and TailwindCSS.
  * **HIL Mission Control**: Human-in-the-Loop administrative dashboard for monitoring system health and SRE alerts.
  * **CLI & API**: Headless triggers via FastAPI endpoints and script runners.
* **Input Types**:
  * Portfolio CSV files (`Portfolio.csv` / `portfolio_example.csv`).
  * Indian equity ticker symbols (`.NS` / `.BO`).
  * Watchlist queries and natural language market prompts.

### 2. Frontend & Ingestion Layer
* **FastAPI Gateway & Streamlit Engine**: Routes incoming requests, streams real-time execution progress, and manages state.
* **Input Validation & Sanitization**:
  * **CSV Validation**: Validates tickers, portfolio weights, and column formatting.
  * **Unicode Scrubbing**: Sanitizes emojis, special markers, and unhandled characters across input buffers.
  * **Error Toasting**: Intercepts runtime provider warnings without interrupting user workflows.

### 3. Backend & Agentic Core (LangGraph Engine)
* **API Gateway & Security**: Handles authentication, rate limiting, request routing, and Web Application Firewall (WAF) filtering.
* **LangGraph State Engine**: Stateful parallel execution engine replacing linear funnels for low-latency multi-agent reasoning.
* **Session & Memory Service**: Maintains user preferences, portfolio context, risk tolerance, and historical query states.
* **Context & Symbol Standardizer**: Automatically appends `.NS` (National Stock Exchange) or `.BO` (BSE) suffixes to raw Indian stock tickers.

### 4. AI Processing & Agent Roster
* **Safety & Policy (Input)**: Input sanitization, prompt injection prevention, and Unicode scrubbing.
* **Model Router**: Intelligently routes calls to **Gemini 3.0 Flash** or **Gemini 3 Flash Preview** based on context depth, speed requirements, and task complexity.
* **10 Core LangGraph Agent Nodes**:
  1. **Retrieval Node**: Gatekeeper validating symbols and fetching historical OHLCV data via `yfinance`.
  2. **Strategy Node**: Macro-economic regime classifier (analyzing VIX, DXY, US 10Y Yields into Goldilocks/Panic regimes).
  3. **Sentiment Node**: Parses latest market news via `Newspaper3k` and calculates fear/greed sentiment scores.
  4. **Technical Node**: Calculates Triple Concordance (MTC) and identifies key support/resistance levels.
  5. **Traditional Node**: Evaluates seasonal patterns and **Muhurtham Trading** windows.
  6. **Dividend Node**: Analyzes yield quality, payout trends, and corporate action impacts.
  7. **Sector Node**: Evaluates sector-wide relative strength and institutional capital rotation.
  8. **Forensic Node**: Audit engine identifying fundamental outliers, accounting red flags, and self-corrections.
  9. **Shadow Node**: Combines technical and sentiment signals to detect **Institutional Bull/Bear Traps**.
  10. **Reporting Node**: Synthesizes multi-agent outputs, generates Markdown summaries, and formats JSON for UI rendering.
* **Safety & Policy (Output)**: Output schema validation, red-flag sanitization, and compliance auditing.

### 5. Tools, Data Sources & Satellites
* **Rover Tools (Agent Actions)**:
  * `batch_scrape_news`: Parallel news scraping via `Newspaper3k` and Google Search API.
  * `batch_get_stock_data`: Parallel price & volume retrieval via `yfinance`.
  * `fetch_block_deals`: Tracks institutional bulk and block deals on NSE/BSE.
  * Technical Indicators & MTC calculator.
* **Data & Storage**:
  * **Cloud SQL (PostgreSQL)**: Connected via Unix socket DSNs with lazy-loading (`asyncio.Lock()`).
  * `/reports` Directory: Storage for generated JSON and Markdown research reports.
  * `metrics/*.jsonl`: Structured crash logs (`errors_*.jsonl`), daily latency, and workflow metric streams.
* **Federated Satellites**:
  * **Investbrand Rover**: Gamified stock discovery challenges.
  * **Pledge-Rover**: Promoters' share pledge tracking.
  * **GitHub Actions Cron Jobs**: Automated daily issue reports and weekly backtests posted to GitHub Discussions.

### 6. Response & Report Delivery
* **Streaming Synthesis**: Real-time task progress and step-by-step agent updates delivered to the UI.
* **Formatted Outputs**: Executive Summary, Technical Level Tables, Traps/Shadow Signals, and PDF/MD/JSON Reports.
* **Delivery Targets**: Streamlit Dashboard, HIL Mission Control, and GitHub Discussions.

---

## ⚙️ Cross-Cutting Services & Performance Optimizations

| Category | Component / Strategy | Description |
| :--- | :--- | :--- |
| **Observability** | `metrics/errors_*.jsonl` & `logs/` | Real-time crash metrics with full trace context, user variables, and log rotation. |
| **SRE & Governance** | Hotfix Agent & Dependabot | Autonomous exception interception and automated dependency management. |
| **Performance** | The Batch Imperative | Enforces batch API calls across tickers instead of sequential iteration. |
| **Database Resilience** | Lazy-Loading DB Connections | Eliminates `Errno 111` race conditions during Cloud Run secret injection. |
| **GoA Parity** | Green-on-Arrival Standards | Strict Python 3.13 compatibility, UTF-8 compliance, and build integrity scripts. |

---

## 🔁 End-To-End Request Flow

```
[User Request / CSV Upload]
          │
          ▼
[Streamlit / React UI] ──▶ [FastAPI Gateway]
                                 │
                                 ▼
                    [Symbol Validation & Retrieval Node]
                                 │
                                 ▼
                     [Macro Strategy Node]
                                 │
      ┌──────────────────────────┼──────────────────────────┐
      ▼                          ▼                          ▼
[Sentiment Node]        [Technical Node]          [Forensic/Sector Nodes]
      │                          │                          │
      └──────────────────────────┼──────────────────────────┘
                                 │
                                 ▼
                     [Shadow Trap Detector]
                                 │
                                 ▼
                 [Gemini LLM Synthesis & Tools]
                                 │
                                 ▼
                       [Report Synthesizer]
                                 │
                                 ▼
                     [Formatted UI / PDF Output]
```

---

## 💡 Key Architectural Takeaways

1. **Stateful Parallel Multi-Agent Intelligence**: Built on LangGraph to execute analytical nodes concurrently, significantly reducing report generation latency.
2. **Powered by Gemini 3.0 Flash**: Delivers rapid, context-aware financial reasoning tailored for Indian stock market dynamics.
3. **Institutional Trap Detection**: Shadow Node merges technical levels with sentiment score divergence to spot institutional bull/bear traps.
4. **Production Hardened (GoA)**: Designed with Green-on-Arrival standards, lazy-loaded database sockets, and federated satellite failure reporting.
