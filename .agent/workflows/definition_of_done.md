---
description: Active Checklist / Definition of Done for every major feature or fix
---

# ✅ Active Checklist (Definition of Done)

Run this checklist before marking any significant task as "Completed".

1.  **Documentation Sync**
    - [ ] Did you update `README.md` if the UI or Features changed?
    - [ ] Did you update `AI_AGENTS.md` if agent logic changed?

2.  **Security & Safety**
    - [ ] Are hardcoded secrets removed?
    - [ ] Is input sanitization active for new inputs?
    - [ ] Is the Investment Disclaimer visible in new tabs?

3.  **Code Consistency**
    - [ ] Did you verify imports work in **Python 3.13** (Global Standard)?
    - [ ] Are new files correctly placed in `rover_tools/` or `tabs/`?

4.  **Audit Trail**
    - [ ] If this was a major release, did you update `FINAL_AUDIT_CHECKLIST.md`?

5.  **Clean Up**
    - [ ] Remove temporary files or debug prints.

6.  **CI/CD & Infrastructure Stability**
    - [ ] **CRITICAL**: No emojis or non-standard Unicode in `.github/workflows/`, `Dockerfile`, or `.env`.
    - [ ] **MANDATORY**: Run `python scripts/build_integrity_check.py` and ensure the output is `[SUCCESS]`.
    - [ ] Ensure all Dockerfiles (including satellite modules) use `python:3.13-slim`.
    - [ ] Ensure `Notify HIL on Failure` step is present and traceable.
