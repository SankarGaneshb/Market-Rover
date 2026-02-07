# 📖 Market-Rover User Guide

Welcome to **Market-Rover**, your AI-powered stock intelligence system. This guide will help you navigate the features and get the most out of your analysis.

---

## 🚀 Getting Started

1.  **Launch**: The app is accessible via your browser (local or hosted URL).
2.  **Navigation**: Use the sidebar on the left to switch between different modules (Tabs).
3.  **Disclaimer**: Always review the legal disclaimer at the bottom of the screen.

---

## 📂 Tab 1: Portfolio Analysis

**Purpose**: Deep-dive intelligence reports for your portfolio.

### How to Use:
1.  **Input Method**:
    *   **Upload CSV**: Upload a CSV file with columns: `Symbol`, `Company Name`, `Quantity`, `Average Price`.
    *   **Manage Portfolios**: Manually create or edit portfolios directly in the app.
2.  **Analyze**: Click **"🚀 Analyze Portfolio"**.
3.  **Process**:
    *   The AI agents (Researcher, Fundamentals, Technicals, Analyst) will process each stock.
    *   Progress bars show real-time status.
4.  **View Reports**: Once complete, reports are saved to `reports/<username>/`. You can view them in the "Recent Reports" section or the dedicated viewer.

---

## 📈 Tab 2: Market Visualizer

**Purpose**: Quick technical snapshots and support/resistance levels.

### Key Features:
*   **One-Click Snapshot**: Select a stock (or use the default) and click "Generate Snapshot".
*   **OI Walls**: Visualizes Open Interest to show where "Smart Money" is betting (Support/Resistance).
*   **Volatility Bands**: See price action relative to statistical volatility.
*   **AI Outlook**: A concise Bull/Bear/Neutral verdict from the AI.

> **Tip**: Use this for a pre-market check on your key holdings.

---

## 🔥 Tab 3: Monthly Heatmap & Forecast (V4.1)

**Purpose**: Historical seasonality analysis and long-term price prediction (2026).

### How to Use:
1.  **Select Ticker**: Choose from the dropdown or enter a custom symbol (e.g., `RELIANCE.NS`).
2.  **Robust Mode (Exclude Outliers)**:
    *   ✅ **Check this box** to remove extreme volatility events (e.g., COVID crash) from calculations.
    *   This makes the "Average Return" and "Seasonality" more representative of *normal* market behavior.
3.  **Visualizations**:
    *   **Heatmap**: Green/Red matrix showing monthly returns since IPO.
    *   **Seasonality**: Bar charts showing "Win Rate" (probability of green month) and "Avg Return".
4.  **2026 Forecast**:
    *   The app backtests two strategies (Median vs Standard Deviation) and picks the winner.
    *   Displays **Conservative**, **Baseline**, and **Aggressive** price targets for Dec 2026.
    *   **Download**: Use the "📥 Download Matrix" button to save the heatmap data.

---

## 📊 Tab 4: Benchmark Index Analysis

**Purpose**: Same powerful tools as Tab 3, but optimized for Indices (Nifty 50, Bank Nifty).

*   Use this to understand the broader market trend before analyzing individual stocks.

---

## 🎯 Tab 5: Forecast Tracker

**Purpose**: Track the performance of the AI's predictions over time.

*   **Save Forecast**: In Tab 3/4, click "💾 Save Forecast" to add a prediction here.
*   **Real-Time Tracking**: This tab updates live prices to show if the prediction is In-the-Money (ITM) or Out-of-the-Money (OTM).
*   **Management**: Delete old or invalid forecasts using the checkbox system.

---

## 🕵️ Tab 6: Shadow Tracker & Forensics

**Purpose**: Advanced "Smart Money" detection.

*   **Shadow Score**: Detects "Silent Accumulation" (institutional buying without price spikes).
*   **Spider Web**: Identifies sector rotation trends.
*   **Forensic Checks**: red flags in accounting (Beneish M-Score, Altman Z-Score).

---

## 💡 Best Practices

*   **Rate Limits**: The app limits requests (e.g., 30 per minute) to prevent API bans. If you see a warning, wait a few seconds.
*   **Cost Control**: The "System Health" or sidebar metrics show generic API usage. The generic Gemini API key is free but has daily quotas.
*   **Data Accuracy**: Data comes from `yfinance` and `NSE`. Occasional delays may occur.

---
## 📢 Automated Intelligence

Market-Rover works for you even when you're sleeping. Check the [GitHub Discussions](https://github.com/SankarGaneshb/Market-Rover/discussions) tab for:

1.  **Daily Market Reports**: Posted every day at 00:00 UTC. Covers Nifty trends, Sector Rotation, and Key Insights.
2.  **Weekly Strategy Backtest**: Runs every Sunday.
    *   **Email Reports**: Receive a top-performers summary directly to your inbox.
    *   **Setup**: Add your SMTP details (Gmail, Outlook, etc.) to `.streamlit/secrets.toml`:
        ```toml
        [email]
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = "your-email@gmail.com"
        sender_password = "your-app-password"
        recipient_email = "recipient@example.com"
        ```

---

*Market-Rover V4.2*
