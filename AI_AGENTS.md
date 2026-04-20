# 🤖 Market-Rover Agentic AI Constitution

This document serves as the **Single Source of Truth** for the Agentic AI system within Market Rover. It details the roles, responsibilities, capabilities, and interactions of every agent in the ecosystem.

---

## 🧠 The Hybrid Intelligence Funnel
The agents operate in a high-fidelity pipeline mimicking a hedge fund's decision-making process:
`Portfolio Manager` -> `Strategist` -> `Sentiment` -> `Technical Analyst` -> `Shadow Analyst` -> `Report Writer`.

---

## 🕵️ Headless Execution (Automated Governance)
Beyond user interaction, the **Strategist** and **SRE Agents** maintain the system autonomously through:
1.  **Daily Market Intelligence**: Automated logic posting to GitHub Discussions.
2.  **Federated Satellite Monitoring**: Real-time failure alerts from **Investbrand** and **Pledge-Rover** sent to the HIL Dashboard.

---

## 🕵️ Agent Roster (Core & Satellite)

### 1-6. Core Analysis Crew
*Orchestrated by Gemini 3.0-Flash (Production Standard).* 🟢
*   **Portfolio Manager**: The Gatekeeper. Validates tickers and standardizes inputs.
*   **Market Strategist**: The Macro-Economist. Monitors global cues (Crude, Gold, Nasdaq) and corporate actions.
*   **Sentiment Analyzer**: The Psychologist. Classifies news as Positive/Negative/Neutral.
*   **Technical Analyst**: The Technician. Focuses purely on Price Action, Support, and Resistance.
*   **Shadow Analyst**: The Forensic Detective. Compares Sentiment vs. Order Flow to detect **Bull/Bear Traps**.
*   **Report Writer**: The Editor. Synthesizes all inputs into the final Intelligence Report.

### 7-11. Satellite & SRE Crew
*Orchestrated by Gemini 3.0-Flash and Node.js.*
*   **Investbrand Puzzle Agent**: Generates the "Brand to Stock" gamified challenges.
*   **Adaptive Teacher**: Contextualizes gameplay with micro-learning insights.
*   **Operational SRE Support**: Intercepts runtime exceptions and routes critical failures to the **HIL Mission Control**.

---

## 📜 Global Agent Rules (Governance Framework)

### 1. The Batch Imperative
*   **Rule**: Never iterate through stocks sequentially. Always use `Batch Tools`.
*   **Reason**: Performance and token efficiency.

### 2. The Low-Latency Directive
*   **Rule**: Strict `max_iter` limit (3-5). No infinite reasoning loops.

### 3. The Ironclad Security Rule
*   **Rule**: Never log or output secrets. Sanitize every agent input via `utils/security.py`.

### 4. The Resilience Protocol
*   **Rule**: Fail gracefully. Fallback from Option Chains to Historical Volatility if data is missing.

### 5. The Production Standard
*   **Rule**: Primary Brain must be **Gemini 3.0-Flash**. Verify UTF-8 compliance and Python 3.13 compatibility before every push.

### 6. The Unicode Scrub Rule
*   **Rule**: **No emojis** in `.github/workflows/`, `Dockerfile`, or `.env`. Use standard text markers like `[ALERT]`.

### 7. The Multi-Provider Social Governance Shield
*   **Rule**: Maintain **Open Access** while protecting the UI.
*   **Reason**: Clients should never see technical provider errors (e.g. "Invalid App ID").
*   **Implementation**: If a provider uses a placeholder ID, the **Social Manager Shield** must intercept and show a friendly internal warning.

### 8. The Federated Satellite Rule
*   **Rule**: Every satellite module (Investbrand, Pledge-Rover) MUST report failures to the central HIL Dashboard.
*   **Reason**: Eliminates "Silent Failures" and ensures total system transparency.

---

## 📊 Agent KPI Matrix
| Agent | Primary KPI | Target | Measuring Logic |
| :--- | :--- | :--- | :--- |
| **Strategist** | Funnel Integrity | >90% | Successfully links Macro -> Micro news. |
| **SRE Agent** | Deployment Stability | 100% | Zero syntax regressions reaching main. |
| **SRE Agent** | TTR (Hotfix) | < 15m | Autonomous recovery time for CI incidents. |

---

**Built with CrewAI, Gemini 3.0-Flash, and Google Cloud Run.** 🚀
*Last Unified Update: April 13, 2026*
