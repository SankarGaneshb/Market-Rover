# 🤖 Market Rover AI Agent Architecture

This document serves as the **Single Source of Truth** for the Agentic AI system within Market Rover. It details the roles, responsibilities, capabilities, and interactions of each agent in the `CrewAI` assembly.

> **MAINTENANCE NOTE:** This file must be updated whenever changes are made to `agents.py` or `tasks.py`.

---

## 🧠 The Hybrid Intelligence Funnel
The agents operate in a sequential pipeline designed to mimic a hedge fund's decision-making process:
`Portfolio Manager` -> `Strategist` -> `Sentiment` -> `Technical` -> `Shadow Analyst` -> `Report Writer`

---

## 🕵️ Agent Roster

### 1. Portfolio Manager (Agent A)
*   **Source:** `agents.py` -> `create_portfolio_manager_agent`
*   **Role:** The Gatekeeper
*   **Goal:** Read and process the user's stock portfolio to ensure accurate tracking.
*   **Key Responsibilities:**
    *   Reads `.csv` portfolio inputs.
    *   Standardizes symbols (e.g., appending `.NS` for NSE).
    *   Validates data integrity before passing it downstream.
*   **Tools:** `read_portfolio`

### 2. Market Impact Strategist (Agent B)
*   **Source:** `agents.py` -> `create_news_scraper_agent`
*   **Role:** The Macro-Economist
*   **Goal:** Identify multi-layered market risks by monitoring macro events, global cues, and specific news.
*   **Key Responsibilities:**
    *   **Macro Scan:** Checks Crude, Gold, Nasdaq, and USD/INR.
    *   **Official Data:** Monitors Board Meetings, Results, and Dividends.
    *   **Funnel Logic:** Connects global events to portfolio stocks (e.g., "Crude up -> Paints down").
*   **Tools:** 
    *   `search_market_news` (Macro)
    *   `get_global_cues` (Indices/Commodities)
    *   `get_corporate_actions` (Official NSE data)
    *   `batch_scrape_news` (Portfolio specific)

### 3. Sentiment Analysis Expert (Agent C)
*   **Source:** `agents.py` -> `create_sentiment_analyzer_agent`
*   **Role:** The Psychologist
*   **Goal:** Quantify market emotion (Fear vs. Greed).
*   **Key Responsibilities:**
    *   Classifies news sentiment as Positive, Negative, or Neutral.
    *   **Critical Output:** Flags "Extreme Sentiment" (Panic/Euphoria) which is the primary input for the Shadow Analyst's trap detection.
*   **Tools:** *Reasoning only context-aware Agent*

### 4. Technical Market Analyst (Agent D)
*   **Source:** `agents.py` -> `create_market_context_agent`
*   **Role:** The CMT (Chartered Market Technician)
*   **Goal:** Analyze Price Action, Trends, and Levels.
*   **Key Responsibilities:**
    *   Ignores news entirely; focuses only on the Chart.
    *   Determines Trend (Uptrend/Downtrend) and Support/Resistance.
    *   Provides the "Where" to the Strategist's "Why".
*   **Tools:** 
    *   `analyze_market_context`
    *   `batch_get_stock_data`

### 5. Institutional Shadow Analyst (Agent G)
*   **Source:** `agents.py` -> `create_shadow_analyst_agent`
*   **Role:** The Forensic Detective
*   **Goal:** Detect Market Traps (Accumulation/Distribution) by comparing Sentiment vs. Flow.
*   **Key Responsibilities:**
    *   **Silent Accumulation:** Detects when Retail is fearful (Sentiment) but Smart Money is buying (Block Deals/Support).
    *   **Bull Traps:** Detects when Retail is euphoric but Price is hitting resistance.
    *   Uses 'Trap Indicators' to find divergences.
*   **Tools:** 
    *   `analyze_sector_flow_tool`
    *   `fetch_block_deals_tool`
    *   `batch_detect_accumulation`
    *   `get_trap_indicator_tool`

### 6. Intelligence Report Writer (Agent E)
*   **Source:** `agents.py` -> `create_report_generator_agent`
*   **Role:** The Editor
*   **Goal:** Synthesize all insights into a comprehensive weekly report.
*   **Key Responsibilities:**
    *   Aggregates the "Intelligence Mesh" (Strategy + Technicals + Shadow).
    *   Produces the actionable Executive Summary and Risk Highlights.
    *   Formats the output for the Streamlit UI.
*   **Tools:** *Reasoning only context-aware Agent*

### 7. Market Data Visualizer (Agent F)
*   **Source:** `agents.py` -> `create_visualizer_agent`
*   **Role:** The Artist
*   **Goal:** Generate premium visual dashboards.
*   **Key Responsibilities:**
    *   Creates visual market snapshots (Charts).
    *   Visualizes Volatility and Option Chains.
*   **Tools:** `generate_market_snapshot`
