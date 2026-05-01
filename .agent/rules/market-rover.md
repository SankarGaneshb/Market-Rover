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

- **Default LLM:** `google-gemini-3.0-flash` (or the latest equivalent configured via `langchain-google-genai`). [file:2]
- **Fallback / long-context model:** `google-gemini-3.0-flash` for longer reasoning tasks (e.g., detailed portfolio reports). [file:2]

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
   - Every satellite module (e.g., `investbrand`) must be import-verifiable without environment variables or credentials.
   - Always run the "Startup Integrity" check: `python -c "from <module>.backend.src.server import app"`.
   - When modularizing API routes, aggressively delete old inline endpoints in the main server file to prevent silent `NameError` route shadowing.
3. **Dependency Sync**:
   - When tools in `rover_tools/` are updated, ensure satellite rovers' `requirements.txt` and Dockerfiles are updated to match.
   - Use absolute imports (e.g., `from rover_tools.logger import ...`) and ensure `PYTHONPATH` includes the app root.
4. **Proxy & Auth Compliance**:
   - **Nginx**: Never use `proxy_set_header Host $host;` when proxying from an Nginx container to a `.run.app` service, as it causes SNI mismatches (502 Bad Gateway).
   - **OAuth**: Always use `urllib.parse.urlencode()` for generating OAuth Redirect URIs instead of string concatenation or `.quote()`, to ensure strict Google security compliance.
