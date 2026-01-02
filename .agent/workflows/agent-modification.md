---
description: Workflow for modifying or adding AI Agents and Tasks
---

# Agent & Task Modification Workflow

**CRITICAL**: `AI_AGENTS.md` is the Single Source of Truth. Code and Docs must match perfectly.

1.  **Strategic Impact Analysis (New & Critical)**
    - [ ] **Role Clarity Check**:
        - Open `AI_AGENTS.md` and review the "Agent Roster".
        - Ask: "Does this change blur the lines between agents?"
    - [ ] **Synergy Check**:
        - How does this agent's output feed the *next* agent?
    - [ ] **Duplication Audit**:
        - Verify no other agent is already fetching/processing this specific data point.

2.  **Pre-Code Compliance & Flexibility**
    - [ ] **Rule Check**: Read `AI_AGENTS.md` "Global Agent Rules" section.
    - [ ] **Exception Protocol**:
        - *Scenario*: If a rule (like "No Loops") MUST be broken for a valid reason (e.g., API strict rate limits requiring sequential calls).
        - *Action*: You must propose a **Trade-off Decision** to the user.
        - *Format*: "I need to break Rule X because of Y. The cost is Z (e.g. slower). Do you approve?"
        - *Constraint*: Do not proceed until approved.

3.  **Implementation**
    - [ ] Modify `agents.py` (Define Agent).
    - [ ] Modify `tasks.py` (Define Task).
    - [ ] Modify `crew.py` (Register Agent/Task).
    - [ ] **Constraint**: Ensure `max_iter` is set correctly (3-5) as per "Low-Latency Directive".

4.  **Documentation Synchronization (Mandatory)**
    - [ ] **Update `AI_AGENTS.md`**:
        - [ ] Add/Update the Agent in "Agent Roster".
        - [ ] Update "Task Mappings" table.
        - [ ] **Document Exceptions**: If an exception was approved, note it as a "Special Exception" in the docs so it's not flagged as a bug later.

5.  **Verification**
    - [ ] **Import Check**: Run `python -m py_compile agents.py tasks.py` to ensure imports are valid.
    - [ ] **Flow Check**: Ensure data flows logically from Previous Task -> This Task -> Next Task.

6.  **Final Polish**
    - [ ] Commit message should reference "Agents Update".
