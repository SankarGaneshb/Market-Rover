---
trigger: always_on
---

# 🧠 Gemini & Agent Rules – Market‑Rover

This document defines **how Gemini is used inside the Market‑Rover repository only** – including models, environment configuration, and strict rules for all AI agents. It complements `README.md` (user-facing) and `AI_AGENTS.md` (architecture-facing). [file:2][file:3]

---

## 1. Scope & Purpose

- This file applies **only to the Market‑Rover workspace** (this repository) and is not intended as a global Gemini config for other projects. [file:2]
- It is the **single source of truth** for:
  - Which Gemini models to use.
  - How agents should reason, respond, and respect data/tool boundaries.
  - Safety, cost, and performance constraints specific to this app. [file:2][file:3]

Whenever `agents.py`, `tasks.py`, or Gemini integration logic changes, update this file together with `AI_AGENTS.md`. [file:3]

---

## 2. Models & API Configuration

### 2.1 Primary model

- **Default / Primary LLM:** `gemini-3.8-flash` (configured via `config.PRIMARY_LLM_MODEL`, `langchain-google-genai`, and `crewai`). [file:2]
- **Fallback / Failover model:** `gemini-3.5-flash` (`config.FALLBACK_LLM_MODEL`) with automatic retry cascade and exponential jitter backoff. [file:2]
- **Ultra-Lite SRE / Webhook model:** `gemini-3.5-flash-lite` (`config.LITE_LLM_MODEL`) for operational diagnostics, fast triage, and SRE alerts. [file:2]

### 2.2 API keys & environment

- Required env var in `.env` (local): [file:2]
  ```bash
  GOOGLE_API_KEY=your_gemini_api_key_here
  ```

---

## 3. Green-on-Arrival (GoA) Standards

To maintain build stability, all code changes MUST adhere to these GoA rules:

1. **Database Robustness**:
   - Never use `google-cloud-sql-connector` at the top level of a module.
   - Always URL-encode database credentials using `urllib.parse.quote_plus` in DSN construction.
   - For Cloud SQL Unix sockets, use the directory path (e.g., `/cloudsql/INSTANCE_NAME`) as the host; do NOT append `.s.PGSQL.5432` as the driver adds it automatically.
   - **Lazy-Loading**: DB Connections MUST use lazy-loading (`asyncio.Lock()`) and NEVER initialize at the global module level to avoid `Errno 111` race conditions during Cloud Run secret injection.
2. **Import Integrity & Route Shadowing**:
   - Every integrated module (e.g., `investbrand`, `ownerise`, `pledge_rover`) must be import-verifiable without environment variables or credentials.
   - Always run the "Startup Integrity" check: `python -c "import server; print('[OK] Unified server loaded successfully')"`.
   - When modularizing API routes, aggressively delete old inline endpoints in the main server file to prevent silent `NameError` route shadowing.
3. **Dependency Sync & Container Optimization**:
   - Production Cloud Run deployments MUST use `requirements-prod.txt` to keep container image sizes minimal and strictly within Artifact Registry free tier quotas.
   - Root `requirements.txt` inherits `-r requirements-prod.txt` and supplies developer/UI tools (`streamlit`, `matplotlib`, `seaborn`, `pytest`) for local development, Snowflake, and CI hooks.
   - When tools in `rover_tools/` are updated, ensure integrated modules' `requirements.txt`, `requirements-prod.txt`, and the root unified `Dockerfile` are updated to match.
   - Use absolute imports (e.g., `from rover_tools.logger import ...`) and ensure `PYTHONPATH` includes the app root.
4. **Proxy & Auth Compliance**:
   - **Nginx**: Never use `proxy_set_header Host $host;` when proxying from an Nginx container to a `.run.app` service, as it causes SNI mismatches (502 Bad Gateway).
   - **OAuth**: Always use `urllib.parse.urlencode()` for generating OAuth Redirect URIs instead of string concatenation or `.quote()`, to ensure strict Google security compliance.
5. **Cost Governance & Zero-Cost GCP Architecture**:
   - **Secret Manager**: Keep active secret versions strictly $\le 6$ (Free Tier limit). Always destroy disabled/obsolete secret versions (`gcloud secrets versions destroy`).
   - **Cloud Storage (GCS) Staging Purge**: Always maintain a 1-day auto-delete lifecycle policy on `*_cloudbuild` staging buckets and clear soft-delete retention. Source history is permanently backed up via GitHub Git history, compiled images in Artifact Registry, and live zero-downtime rollbacks via Cloud Run Revisions.
6. **Frontend & Asset Integrity (Deep Health)**:
   - Every integrated frontend SPA (`market_rover`, `hil_rover`, `investbrand`, `pledge_rover`) MUST pass deep asset verification via `python scripts/verify_frontend_health.py` and `pytest tests/test_frontend_integrity.py`.
   - Never rely solely on HTTP 200 status codes: the verification MUST confirm the root DOM mount element (`<div id="root">`), parse and validate that every referenced `<script src="...">` and `<link rel="stylesheet">` asset exists on disk, returns HTTP 200 with non-empty content, and is NOT returning an erroneous fallback HTML string.
   - Guard against browser script MIME-type crashes by ensuring non-existent static assets return HTTP 404 JSON rather than SPA fallback HTML.
