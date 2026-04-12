
# 🛠️ Market-Rover Operational Manual

This guide covers how to handle operational issues that require manual intervention. The system is designed to heal itself from minor glitches (retries), but some issues demand a human touch.

## 🚨 Troubleshooting & Manual Fixes

### 1. LLM Failures (CrewExecutionError)
**Status**: Partially Automated (3 Retries)
**Symptom**: "Invalid response from LLM call" or "ValueError" in logs.
**Action**:
1.  **Check Logs**: Go to `logs/market_rover.log`.
2.  **Verify Quota**: Ensure your Gemini API key hasn't hit its rate limit or monthly quota.
3.  **Manual Restart**: If retries fail 3 times, the API might be down or blocked.
    *   Wait 15 minutes.
    *   Restart the server: `python app.py` (or restart the Docker container).

### 2. Dependency Issues (ImportError)
**Status**: Manual Fix Required
**Symptom**: "cannot import name 'xyz'" or "ModuleNotFoundError".
**Action**:
1.  **Rebuild Environment**: Dependencies might be out of sync.
    ```powershell
    # Windows
    deactivate
    rm -r .venv
    python -m venv .venv
    .\.venv\Scripts\Activate
    pip install -r requirements.txt
    ```
2.  **Check Deployment**: If on Streamlit Cloud, check `packages.txt` and `requirements.txt`.


### 3. Missing Data Files (FileNotFoundError)
**Status**: Manual Fix Required
**Symptom**: "File not found: Portfolio.csv"
**Action**:
1.  **Upload Data**: Ensure `Portfolio.csv` is present in the root directory.
2.  **Format Check**: Ensure it has columns: `Symbol`, `Qty`, `Avg Price`.

### 4. API Connection Errors (Shadow Tracker)
**Status**: Automated Warning / Retry
**Symptom**: "⚠️ Connection Error" on the Shadow Tracker tab or "Warning" in logs.
**Cause**: The external NSE data source is down, busy, or blocking requests (common during off-hours).
**Action**:
1.  No action required usually; the system retries automatically (3 times).
2.  If persistent (>24 hours), check `logs/market_rover.log` for "API Down" patterns.
3.  **Mine Logs**: Run `python scripts/mine_logs.py` to see failure timestamps and frequency.

### 5. Automated Workflow Failures
**Status**: GitHub Actions / Dependabot
**Symptom**: "Daily Report" didn't post, or Dependabot PR didn't merge.
**Action**:
1.  **Check Actions Tab**: Go to `Actions` -> `Daily Issue Report` or `Dependabot Automation` to see the failure log.
2.  **Dependabot**:
    *   If auto-merge failed, check if the "checks" passed (e.g. tests).
    *   Manually merge if it's a safe update.
3.  **Backtest**:
    *   If data is missing for `batch_backtester.py`, verify `yfinance` is up.

### 6. CI/CD & Build Failures (Market-Rover Build)
**Status**: Managed by SRE Support Sentinel (Autonomous Response)
**Symptom**: GitHub Actions red-dot on `main` or `HIL-Rover`.
**Safeguard**:
1.  **Pre-Flight Integrity Check**: Every build starts with `scripts/build_integrity_check.py`.
2.  **SRE Agent Escalation**: If a build fails, the **SRE Support Sentinel** (Gemini-powered) analyzes the logs and proposes a remediation to the HIL Dashboard.
**Action (Developer)**:
1.  **Run Integrity Check Locally**: `python scripts/build_integrity_check.py` to confirm fixing the regression before pushing.
2.  **Review HIL Dashboard**: Approve SRE-proposed code or infrastructure fixes.

### 7. Microservice Startup Errors (Cloud Run)
**Status**: Manual Fix Required
**Symptom**: "The user-provided container failed to start and listen on the port... PORT=8080"
**Common Causes**:
1.  **ModuleNotFoundError**: (Python) Occurs if `__init__.py` files are missing in parent directories, preventing the server (e.g., Uvicorn) from importing the application.
    *   **Fix**: Add empty `__init__.py` files to `backend/` and `src/` folders of the microservice.
2.  **Hardcoded Port**: Container listens on a port other than 8080.
    *   **Fix**: Ensure `uvicorn` (Python) or `node` (JS) is bound to `0.0.0.0:8080`.
3.  **Missing Node Engine**: (Node.js) Occurs if the required Node version is not matched by the Docker base image.
    *   **Fix**: Update `FROM node:XX-alpine` in the microservice `Dockerfile`.


---

## 🛑 Limitations & Scope

Please note what is **NOT** covered by the automated retry system:

*   **Streamlit UI Crashes**: If the web page freezes or shows a big red traceback box, that is a UI error. You must refresh the page (`F5`).
*   **External CI/CD**: Errors in GitHub Actions or Docker deployment pipelines are outside this application's control. Check the GitHub "Actions" tab.
*   **Infrastructure**: If the server runs out of memory (OOM) or disk space, the application will crash. This requires system-level monitoring.

---

## 📝 Issue Reporting

If you encounter a new bug, please log it using this template.

> **Tip**: Run `python scripts/mine_logs.py` first to extract recent error messages from the logs automatically.

**Bug Report Template**:
```markdown
**Date**: YYYY-MM-DD
**Component**: (e.g., News Scraper, LLM, Web UI)
**Error Message**: (Paste the traceback here)
**Steps to Reproduce**:
1.
2.

**Context**: (e.g., Was the market closed? Was VPN on?)

---

## 🧠 AI Training (Monthly Cycle)

To improve the Agent's accuracy without waiting for organic user activity, run this **Mental Calibration Cycle** once a month.

### Step 1: Feed the Brain (Day 1)
Run the training script to analyze Nifty 50 stocks and generate new predictions.
```powershell
python scripts/train_brain.py
```
*   **What it does**: Overwrites `Portfolio.csv` with top 20 Nifty stocks, runs the full analysis, and saves "Buy/Sell" signals to `data/memory.json`.

### Step 2: Validate Outcomes (Day 7-30)
After market movement has occurred (at least 3 days later), run the validator.
```powershell
python scripts/validate_outcomes.py
```
*   **What it does**: Checks Yahoo Finance for actual price changes. Updates the memory with "Success" or "Fail".
*   **Result**: Agents will see these outcomes in their next run and self-correct (e.g., "I failed on Banking stocks last month, I should be cautious").
```
