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
    - [ ] **STARTUP INTEGRITY** (Added 2026-04-20 — Root Cause: HIL-Rover & Pledge-Rover boot timeouts):
        - After installing deps for any satellite module (hil_rover, pledge_rover, market_rover), verify the app actually loads:
          ```bash
          python -c "from <module>.backend.src.server import app; print('[OK] App loaded')"
          ```
        - This goes BEYOND `py_compile`. It catches missing deps, bad global imports, and blocking startup code.
    - [ ] **DEPS DRIFT CHECK**: If you add a tool import from `rover_tools/`, `utils/`, or `scripts/` into a satellite module, verify the dependency exists in **that satellite's `requirements.txt`**, not just the root `requirements.txt`.
    - [ ] **POST-DEPLOY HEALTH CHECK**: After a Cloud Run deploy, confirm the service is healthy:
        ```bash
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
    - [ ] **STARTUP INTEGRITY** (Added 2026-04-20 — Root Cause: HIL-Rover & Pledge-Rover boot timeouts):
        - After installing deps for any satellite module (hil_rover, pledge_rover, market_rover), verify the app actually loads:
          ```bash
          python -c "from <module>.backend.src.server import app; print('[OK] App loaded')"
          ```
        - This goes BEYOND `py_compile`. It catches missing deps, bad global imports, and blocking startup code.
    - [ ] **DEPS DRIFT CHECK**: If you add a tool import from `rover_tools/`, `utils/`, or `scripts/` into a satellite module, verify the dependency exists in **that satellite's `requirements.txt`**, not just the root `requirements.txt`.
    - [ ] **POST-DEPLOY HEALTH CHECK**: After a Cloud Run deploy, confirm the service is healthy:
        ```bash
        curl -f https://<service-url>/health || echo '[FAIL] Health probe failed'
        ```

7.  **Database Connection Standard** (Added 2026-04-21)
    - [ ] **MANDATORY**: Avoid instantiating `google-cloud-sql-connector` at the module's top-level. This causes import-time authentication failures in CI and local checks.
    - [ ] **STANDARD**: Use manual, socket-based DSN construction for Cloud SQL. **MANDATORY**: Use `urllib.parse.quote_plus()` for all credentials (user/pass) to prevent failures caused by special characters.
    - [ ] **MANDATORY**: For Unix sockets, provide only the directory path (e.g., `/cloudsql/INSTANCE_NAME`) as the host; do NOT append `.s.PGSQL.5432` as the driver adds it automatically.
    - [ ] Example: `postgresql://{quote(user)}:{quote(pass)}@/dbname?host=/cloudsql/conn`. Use `asyncpg` or `sqlalchemy` (async).
    - [ ] Verify that database credentials are never required to simply *import* the server.

8.  **Satellite Build Integrity (Market-Rover v5 Standard)**
    - [ ] **EXPLICIT SYNC**: If a satellite module uses root-level tools (e.g., `rover_tools`, `utils`), ensure the CI workflow has a `Sync Core Dependencies` step using `cp -r` to move those tools into the build context.
    - [ ] **DOCKERFILE COPY**: Verify the satellite's `Dockerfile` has explicit `COPY rover_tools/ ./rover_tools/` commands and sets `ENV PYTHONPATH=/app`.
    - [ ] **DEEP IMPORT VERIFICATION**: Run `python scripts/build_integrity_check.py` and verify it passes the "Deep Import" stage for all rovers.
9.  **AI Model Consistency**
    - [ ] **STANDARD**: Use `google-gemini-3.0-flash` for all primary agent logic.
    - [ ] **SYNC**: If updating a model, verify it matches the configuration in `.agent/rules/market-rover.md`.
