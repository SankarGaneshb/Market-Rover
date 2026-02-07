# 🚀 Market-Rover v4.3 - Release Notes

**Release Date:** Feb 07, 2026
**Version:** v4.3.0
**Status:** **Stable / Production Release**

---

## 🌟 Highlights

**Market-Rover v4.3** introduces a **Strategic 2-Year Trading Calendar** (2026-2027) to help users visualize long-term holding strategies.

### 📅 **Strategic Trading Calendar (New)**
- **Dual-Year Strategy**: Buying opportunities are now mapped to **2026**, with corresponding Selling targets in **2027**.
- **Holiday-Aware**: Dates are automatically adjusted for **NSE Holidays** and weekends for both 2026 and 2027.
- **Enhanced Visualization**: Side-by-side annual calendars for clear Entry (Green) and Exit (Red) planning.

---

# 🚀 Market-Rover v4.2 - Release Notes

**Release Date:** Jan 26, 2026
**Version:** v4.2.0
**Status:** **Stable / Archived**

---

## 🌟 Highlights

**Market-Rover v4.2** introduces enterprise-grade resilience to its data pipeline. We have hardened the market data fetching process to handle exchange outages gracefull by treating BSE as a first-class fallback for NSE.

### 🛡️ **Data Resilience (New)**
- **Exchange Fallback**: Automatically switches to BSE (`.BO`) if NSE (`.NS`) data is unavailable.
- **Smart Retries**: Implemented exponential backoff for network requests to prevent API throttling failures.
- **Test Coverage**: Achieved ~80% test coverage for core analytical engines (`Portfolio`, `Forensic`, `Profiler`).

### 📊 **Institutional Analytics**
- **Forensic Engine**: Validated fraud detection algorithms (Satyam, CWIP, Revenue Quality).
- **Investor Profiler**: Validated "Sleep Test" logic and asset allocation strategies.

---

## 🛠️ Key Fixes & Improvements

1.  **Simulation Graph Fix**: Resolved "No Data" errors for the Hunter/Preserver personas by replacing hollow ETF proxies with reliable liquid assets (GOLDBEES, TRENT).
2.  **Profile Lock**: Fixed a critical bug where the app trapped users in the profile setup screen.
3.  **System Health**: Patched crash report handling (`KeyError` in logs).
4.  **UI/UX**: Removed outdated "v2.0" labels; Unified branding to "Market-Rover".
5.  **Security**: Implemented Rate Limiting and Input Sanitization for tickers.
6.  **Integrity Shield**: Fixed invalid tool definition preventing the Agent from initializing (Switched to CrewAI native tools).
7.  **Shadow Score Integration**: Integrated "Shadow Score" (Institutional Accumulation) directly into the Portfolio Analysis Heatmap for instant visibility.
8.  **Code Hygiene**: Removed ~800 lines of unused "dead code" scripts to improve maintenance and test coverage accuracy.

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
