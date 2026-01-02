---
description: Pre-flight checklist and command flow for deploying to Streamlit Cloud
---

# Deployment Workflow

Streamlit Cloud deploys automatically on push. This workflow ensures that push is safe.

1.  **Codebase Integrity & Hygiene**
    - [ ] **Cleanup**: Remove `print()` statements used for debugging (use `logger` instead).
    - [ ] **No Dead Code**: Remove commented-out blocks that are no longer needed.
    - [ ] **Secrets Check**: **CRITICAL**. Ensure no API keys or hardcoded secrets are in the code.

2.  **Pre-Flight Safety Check**
    - [ ] **Dependencies**: Did you add new libraries?
        - [ ] Run: `pip freeze > requirements.txt` (or manually add packages).
        - [ ] Clean up: Remove local-only tools like `jupyter` or `black` from requirements if present.
    - [ ] **Imports**: Verify no "local-only" imports.
        - [ ] Rule: Use absolute imports `from rover_tools...` instead of `from ..tools`.

3.  **Compilation Check**
    // turbo
    - [ ] Run syntax check on all python files:
      ```powershell
      python -m py_compile app.py agents.py tasks.py crew.py rover_tools/*.py utils/*.py
      ```

4.  **Documentation Check**
    - [ ] **Version Scrub**: Ensure no "V4.0" or "V5.0" strings in `README.md` or `app.py` titles (Rule: "No Versioning").
    - [ ] **Status**: Ensure `README.md` badges (Status/Security) are accurate.

5.  **Deployment Action**
    - [ ] **Commit**: `git add .` -> `git commit -m "feat: [Description]"`
    - [ ] **Push**: `git push origin main`

6.  **Emergency Override Protocol (Hotfix)**
    - *Scenario*: **P0 Incident** (Site Down / Security Leak).
    - *Action*: You may skip Steps 3 & 4 (Compilation/Docs) IF AND ONLY IF:
        1.  The fix is < 5 lines of code.
        2.  You explicitly `notify_user` with "EMERGENCY DEPLOY: [Reason]".
        3.  You CREATE a task to "Backfill Documentation" immediately after the fire is out.
