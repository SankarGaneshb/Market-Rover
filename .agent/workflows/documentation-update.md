---
description: Routine checks to keep documentation fresh and accurate
---

# Documentation Update Workflow

Avoid "Documentation Drift" by running this whenever a user session concludes or a major feature lands.

1.  **⏱️ Start Timer**
    - [ ] Run: `python -m utils.tracking start doc-update`

2.  **Narrative Consistency Check**
    - [ ] **Unified Voice**: Ensure `README` and `AI_AGENTS.md` match.
    - [ ] **Exception Audit**: Look for "Approved Exceptions" and document them.

3.  **README.md Audit**
    - [ ] **Features Table**: Is it complete?
    - [ ] **Tech Stack**: Is it up to date?
    - [ ] **File Structure**: Does it match reality?
    - [ ] **Date**: Update "Last Updated".

4.  **Architecture Sync**
    - [ ] Check `agents.py` vs `AI_AGENTS.md`.

5.  **Audit Checklist**
    - [ ] Update `FINAL_AUDIT_CHECKLIST.md`.

6.  **Badges**
    - [ ] Verify links and badges.

7.  **🏁 Stop Timer**
    - [ ] Run: `python -m utils.tracking stop [SESSION_ID] success`
