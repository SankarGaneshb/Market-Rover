---
description: Routine checks to keep documentation fresh and accurate
---

# Documentation Update Workflow

Avoid "Documentation Drift" by running this whenever a user session concludes or a major feature lands.

1.  **Narrative Consistency Check (Crucial)**
    - [ ] **Unified Voice**: Ensure the `README` and `AI_AGENTS.md` tell the same story.
        - *Check*: If `README` says "We use 5 Agents", `AI_AGENTS.md` must list exactly 5.
    - [ ] **Conflicting Instructions**: Remove old rules if new ones replace them.
    - [ ] **Exception Audit**:
        - *Task*: Look for any "Approved Exceptions" created during development (Flexible Trade-offs).
        - *Action*: Ensure these are noted in the docs (e.g., "Note: This agent uses sequential processing due to API limits").
        - *Reason*: Prevents future devs/agents from "fixing" a deliberate feature.

2.  **README.md Audit**
    - [ ] **Features Table**: Does it list *every* major tab/feature currently in the app?
    - [ ] **Tech Stack**: Are the libraries (e.g. `streamlit`, `crewai`, `gemini-2.0`) up to date?
    - [ ] **File Structure**: Does the text tree match the actual `list_dir` output?
    - [ ] **Date**: Update the "Last Updated" date at the bottom.

3.  **Architecture Sync (`AI_AGENTS.md`)**
    - [ ] Check if `agents.py` matches the "Agent Roster".
    - [ ] Check if `tasks.py` matches the "Task Mappings".

4.  **Audit Checklist (`FINAL_AUDIT_CHECKLIST.md`)**
    - [ ] If a major refactor happened, mark relevant items as Checked/Unchecked.

5.  **Badges & Links**
    - [ ] Verify the "Live App" link works.
    - [ ] Verify Security/Status badges reflect reality.
