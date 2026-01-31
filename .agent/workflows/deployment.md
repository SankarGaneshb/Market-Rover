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
