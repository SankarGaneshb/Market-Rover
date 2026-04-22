---
description: Pre-flight checklist and command flow for deploying to Streamlit Cloud
---

# Deployment Workflow

Streamlit Cloud deploys automatically on push. This workflow ensures that push is safe.

1.  **⏱️ Start Timer**
    - [ ] Run: `python -m utils.tracking start deployment`
    - [ ] Save the Session ID for the end.

2.  **Codebase Integrity & Hygiene**
    - [ ] **Cleanup**: Remove `print()` statements.
    - [ ] **No Dead Code**: Remove commented-out blocks.
    - [ ] **Secrets Check**: Ensure no API keys in code.

3.  **Pre-Flight Safety Check**
    - [ ] **Dependencies**: Run `pip freeze > requirements.txt` if needed.
    - [ ] **Imports**: Verify no "local-only" imports.
    - [ ] **Deps Drift**: If modifying a satellite module that uses shared tools from `rover_tools/`, `utils/`, or `scripts/`, confirm the dependency exists in **that module's own `requirements.txt`**.
    - [ ] **Startup Integrity**: After installing a satellite's deps, verify the app loads:
        ```bash
        python -c "from <module>.backend.src.server import app; print('[OK]')"
        ```
    - [ ] **No Connector at Import**: Ensure no `google-cloud-sql-connector` is instantiated at the top-level of any file. This allows build-time imports to pass without credentials.
    - [ ] **DB Robustness**: Ensure database connection strings use `urllib.parse.quote_plus()` for all credentials (user/password). **MANDATORY**: For Unix sockets, provide only the directory path as the host (e.g., `?host=/cloudsql/conn`).
    - [ ] **Context Sync**: If modifying a satellite, ensure its `.github/workflows/` includes a `Sync Core Dependencies` step.


4.  **Compilation Check**
    // turbo
    - [ ] Run syntax check on all python files:
      ```powershell
      python -m py_compile app.py agents.py tasks.py crew.py rover_tools/*.py utils/*.py
      ```

5.  **Documentation Check**
    - [ ] **Version Scrub**: Ensure no "V4.0" strings.
    - [ ] **Status**: Ensure badges are accurate.

6.  **Deployment Action**
    - [ ] **Commit**: `git add .` -> `git commit -m "feat: [Description]"`
    - [ ] **Push**: `git push origin main`

7.  **Emergency Override Protocol (Hotfix)**
    - *Scenario*: **P0 Incident** (Site Down).
    - *Action*: You may skip Steps 4 & 5 IF < 5 lines + Notify User.
    - *Metric*: Run: `python -m utils.tracking event emergency_override "Reason for hotfix"`

8.  **Post-Deploy Verification**
    - [ ] Open https://market-rover.streamlit.app/
    - [ ] Verify the app loads.

9.  **🏁 Stop Timer**
    - [ ] Run: `python -m utils.tracking stop [SESSION_ID] success`
