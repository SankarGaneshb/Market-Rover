---
description: Workflow for modifying or adding AI Agents and Tasks
---

# Agent & Task Modification Workflow

**CRITICAL**: `AI_AGENTS.md` is the Single Source of Truth. Code and Docs must match perfectly.

1.  **⏱️ Start Timer**
    - [ ] Run: `python -m utils.tracking start agent-modification`
    - [ ] Save the Session ID for the end.

2.  **Strategic Impact Analysis**
    - [ ] **Role Clarity Check**: Ask: "Does this change blur the lines between agents?"
    - [ ] **Synergy Check**: Ensure the data flow is additive.
    - [ ] **Duplication Audit**: Verify no other agent is already fetching this data.

3.  **Pre-Code Compliance & Flexibility**
    - [ ] **Rule Check**: Read `AI_AGENTS.md` "Global Agent Rules" section.
    - [ ] **Exception Protocol**:
        - *Scenario*: If a rule (like "No Loops") MUST be broken.
        - *Action*: Propose Trade-off > Get Approval.
        - *Metric*: If approved, Run: `python -m utils.tracking event flexibility_protocol "Reason for sequential loop"`

4.  **Implementation**
    - [ ] Modify `agents.py` (Define Agent).
    - [ ] Modify `tasks.py` (Define Task).
    - [ ] Modify `crew.py` (Register Agent/Task).
    - [ ] **Constraint**: Ensure `max_iter` is set correctly (3-5).

5.  **Documentation Synchronization (Mandatory)**
    - [ ] **Update `AI_AGENTS.md`**:
        - [ ] Add/Update the Agent in "Agent Roster".
        - [ ] Update "Task Mappings" table.
        - [ ] **Document Exceptions**: Note any approved exceptions.

6.  **Verification**
    - [ ] **Import Check**: Run `python -m py_compile agents.py tasks.py`.
    - [ ] **Flow Check**: Ensure data flows logically.
    - [ ] **Final Polish**: Commit message should reference "Agents Update".

7.  **🏁 Stop Timer**
    - [ ] Run: `python -m utils.tracking stop [SESSION_ID] success`
