---
description: Standard workflow for implementing new features in Market-Rover
---

# Feature Development Workflow

Follow this workflow for every new feature request to ensure consistency and quality.

1.  **Strategic Planning & Impact Analysis**
    - [ ] **Necessity Check**:
        - "Does this feature solve a generic problem or a specific user need?"
        - Verify it fits the "Market-Rover" core mission (Stock Intelligence).
    - [ ] **Duplication Audit**:
        - Search the codebase (`grep_search`) to ensure this logic doesn't already exist in another form (e.g., in `rover_tools/` or `utils/`).
    - [ ] **Architecture Fit**:
        - "Where should this live?" (New tab? Sidebar? Popover?)
        - Ensure it doesn't clutter the UI or degrade performance.
    - [ ] **Flexibility Protocol (Trade-off Check)**:
        - *Question*: "Does this feature require breaking any established constraint (e.g., using a non-standard library or loop for precision)?"
        - *Action*: If YES, you must explicitly **Notify User** with the trade-off (e.g., "This will be slower but 100% accurate").
        - *Rule*: You cannot proceed with a rule violation without explicit User Confirmation.

2.  **Implementation Phase**
    - [ ] **Initialize**: Create/Update `task.md` and `implementation_plan.md`.
    - [ ] **Mode Check**: Ensure you are in `EXECUTION` mode in `task_boundary`.
    - [ ] **Coding**: Implement the changes.
        - *Web Rule*: Use `st.status` or `st.spinner` for long running operations.
        - *Data Rule*: Use `pandas` for data manipulation, avoid raw loops.
    - [ ] **Refine**: If `app.py` gets too large, refactor into `utils/` or `rover_tools/`.

3.  **Verification Phase**
    - [ ] **Mode Check**: Switch to `VERIFICATION` mode.
    - [ ] **Integration Test**: ensure the new feature works *with* existing features, not just in isolation.
    - [ ] **Lint/Compile**: Run `python -m py_compile [modified_files]` to check for syntax errors before pushing.

4.  **Documentation Phase**
    - [ ] **Update README**: Update the "Features" table or "Tech Stack" in `README.md` if new tools/capabilities were added.
    - [ ] **Update Agent Docs**: If agents changed, standard `agent-modification` workflow triggers here.

5.  **Completion**
    - [ ] Update `task.md` to [x].
    - [ ] Notify User with a clear summary of what was done and what needs their review.
