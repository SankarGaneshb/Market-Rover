# 🚀 Market-Rover v4.1 - Release Notes

**Release Date:** Jan 7, 2026
**Version:** v4.1.0-GA
**Status:** **Stable / Production Release**

---

## 🌟 Highlights

**Market-Rover v4.1** is a significant upgrade focusing on stability, data integrity, and institutional-grade analytics. This release marks the transition from "Beta" to a production-ready system.

### 🛡️ **Integrity Shield (New)**
- **Forensic Accounting:** Automatically scans balance sheets for 8 red flags (Benish M-Score, Altman Z-Score).
- **Shadow Radar:** Detects "Smart Money" accumulation before price breakouts.
- **Investor Profiler:** A behavioral finance engine (Sleep Test) that builds a "Smart Portfolio" tailored to your risk persona.

### 📊 **Institutional Analytics**
- **Heatmap 2.0:** Interactive monthly return heatmaps with outlier exclusion logic.
- **Forecast Engine:** AI-driven 2026 price targets using Monte Carlo + Regression models.
- **Simulation**: Backtest your generated strategies against Nifty 50 instantly.

---

## 🛠️ Key Fixes & Improvements

1.  **Simulation Graph Fix**: Resolved "No Data" errors for the Hunter/Preserver personas by replacing hollow ETF proxies with reliable liquid assets (GOLDBEES, TRENT).
2.  **Profile Lock**: Fixed a critical bug where the app trapped users in the profile setup screen.
3.  **System Health**: Patched crash report handling (`KeyError` in logs).
4.  **UI/UX**: Removed outdated "v2.0" labels; Unified branding to "Market-Rover".
5.  **Security**: Implemented Rate Limiting and Input Sanitization for tickers.
6.  **Integrity Shield**: Fixed invalid tool definition preventing the Agent from initializing (Switched to CrewAI native tools).

---

## 📦 Deployment

This version is ready for **Streamlit Community Cloud**.

**Deployment Steps:**
1.  Push `main` branch to GitHub.
2.  Deploy via [share.streamlit.io](https://share.streamlit.io).
3.  Set `GOOGLE_API_KEY` in Secrets.

*(See `DEPLOYMENT.md` for full guide)*

---

## 🔮 What's Next (v5.0 Map)
- **Sector Rotation Dashboard**
- **Automated Weekly Email Reports**
- **User Authentication (Multi-User)**

---

*Market-Rover Team*
