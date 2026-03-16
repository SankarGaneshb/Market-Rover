# Pledge Rover - User Guide

This guide details exactly what the Pledge Rover feature accomplishes, how the background processes work, and how continuous risk assessment is delivered to the user interface.

## 1. What Does Pledge Rover Do?

When promoters of listed Indian companies pledge their shares as collateral for loans, the stock exchanges (BSE/NSE) require disclosures under **SAST Regulation 31**. 

If market conditions crash and a stock hits a "trigger price," lenders forcefully dump the promoter's pledged shares on the open market, causing a catastrophic downward spiral (Contagion). 

**Pledge Rover's single job is to catch these spirals before they happen.** It tells you:
1. Is this pledge safe "Growth" borrowing or desperate "Survival" borrowing?
2. What is the margin call trigger price?
3. What is the promoter's *actual* True Economic Interest (Skin in the Game) after stripping away shell entities?

## 2. The Council of Experts (Agent Roles & Responsibilities)

Pledge Rover replaces standard data parsers with a LangGraph/CrewAI multi-agent pipeline. Each agent is highly specialized with specific goals and backstories to prevent hallucination and ensure thorough analysis.

### I. The Harvester
**Role:** Data Extraction Specialist
**Responsibility:** The Harvester's sole job is to ingest raw Regulation 31 SAST (Substantial Acquisition of Shares and Takeovers) and LODR XBRL/PDF filings from the BSE/NSE feeds. 
**How it works:** It reads the dense, unstructured legalese and extracts only the deterministic facts: Who is the Pledgor? Who is the Pledgee? What exact percentage was encumbered? What is the stated purpose? It normalizes this data into a clean JSON format for the next agent.

### II. The Genealogist
**Role:** Network & Entity Tracker
**Responsibility:** The Genealogist manages the "Shadow Tracker." Its job is to cross-reference the extracted *Pledgee* (the lender) against MCA (Ministry of Corporate Affairs) and LEI databases.
**How it works:** If a promoter pledges to a Tier-1 Bank (like HDFC or SBI) for "Business Expansion," The Genealogist flags it as safe. If the pledge is to an obscure, related-party NBFC, it raises a Red Flag for "Shadow Pledging." It is responsible for calculating the promoter's *True Economic Interest* (Net-Effective Holding) by stripping away shell entities.

### III. The Actuary
**Role:** Quantitative Risk Modeler
**Responsibility:** The Actuary handles the strict mathematics of Contagion Risk.
**How it works:** It takes the Genealogist's output, calculates the Loan-to-Value (LTV) ratio, and runs a reverse formula to find the exact **Margin Call Trigger Price**. It then compares this trigger price against live market feeds. If the current price drops within 15% of the trigger price, The Actuary moves the stock into a "High Contagion / Danger Zone" state.

### IV. The Skeptic
**Role:** Lead Analyst & Synthesizer
**Responsibility:** The Skeptic acts as the final human-like oversight, ensuring numbers aren't taken out of context.
**How it works:** It reviews the Actuary’s math and the Harvester’s stated "purpose." It analyzes Notes to Accounts and recent market actions. *Example: Did the promoter pledge 10% but simultaneously buy 1% from the open market?* It debates the Actuary to determine if this is "Survival Pledging" (desperation) or "Growth Pledging" (expansion). It then issues the final **Governance Score (1-10)** and a natural language summary.

## 3. Feature Breakdown: The Dashboard

The Dashboard is your command center for market-wide risk.

- **Market Metrics Row**: Displays quick data on Active Contagion flags, total liquidity pledged, and promoters tracked.
- **Recent Council Analysis Table**: A real-time feed of promoter filings that have recently been scored by our AI Council. 
  - Each promoter is assigned a **Governance Score (1.0 - 10.0)**. A score below 4 triggers a High Contagion alert.
  - The color-coded progress bars provide instant visual hierarchy so you can scan for danger.

## 3. Feature Breakdown: Target Analysis Profile

Clicking *View Dossier* on a promoter (like Vedanta) takes you to the deep-dive Profile page. This UI is unique because it exposes the AI's "chain of thought" to you, the user.

### A. The Debate Log
Instead of just handing you a number, the UI visualizes a conversation between the specialized AI agents:
1. **The Harvester** reads the dry legalese: *"Twin Star Holdings pledged 98.4% to SBICAP."* 
2. **The Genealogist** digs into the shadows: *"SBICAP is just a trustee. The real money is tied to a $1.2B debt restructuring."*
3. **The Actuary** sounds the alarm: *"LTV is 1.8x. At CMP ₹280, the margin call trigger is ₹255. We are in the Danger Zone (8.9% proximity)."*

This transparency ensures you understand exactly *why* a stock is risky, building immense trust in the tool.

### B. Skeptic Synthesis
The right sidebar displays the **Final Resolution**. The Skeptic Agent consumes the entire debate and provides the human-readable summary: *"This is classic Survival Pledging."* It outputs the true **Net Effective Holding**, stripping away the illusion of large promoter ownership.

## 4. Operational Flow (Behind the Scenes)

While currently mocked for UI demonstration, the designed pipeline works as follows:
1. A cron job or webhook triggers the `POST /api/agents/trigger` endpoint with the text of a newly published BSE filing.
2. The Fast API server invokes LangGraph/CrewAI. 
3. The 4 agents run their sequential tasks (Extract -> Trace -> Quantify -> Debate).
4. Council Output is generated conforming to the Pydantic schema (Governance Score, Final Sentiment).
5. Data is committed via SQL Alchemy to the Cloud SQL PostgreSQL instance (`analysis_runs` and `promoters` tables).
6. The React frontend fetches `/api/promoters/:symbol` to re-render the dashboard.

## Next Steps for Expansion
As you review this feature, consider if you want to:
- Connect the frontend strictly to the BSE Announcements RSS/JSON feed.
- Add historical line charts showing the *change* in pledge percentage over the past 5 years.
- Add an interactive web visualization (nodes and edges) in the UI specifically for The Genealogist's findings on shell companies. 
