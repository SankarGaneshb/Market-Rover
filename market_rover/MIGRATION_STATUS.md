# Market-Rover v5.0 Migration Status

> **Migration Goal**: Replace the root Streamlit `app.py` with a production-grade
> React 19 frontend + FastAPI backend architecture, mirroring the InvestBrand and
> Pledge Rover satellite module patterns. Deployed as two separate Cloud Run services:
> `market-rover-api` (backend) and `market-rover-ui` (frontend).

---

## Overall Progress: Phase 3 of 3 Complete

```
[##########] 100% — All features implemented. Ready for Cloud SQL provisioning and GCP deploy.
```


---

## Phase 1 — Core Architecture (COMPLETE)

| Item | Status | Notes |
|------|--------|-------|
| Backend: FastAPI server (`server.py`) | DONE | Auth, analyze, profile, forecast endpoints |
| Backend: LangGraph graph (`market_rover_graph.py`) | DONE | 10-node parallel graph |
| Backend: Agent nodes (10x) | DONE | retrieval, strategy, sentiment, technicals, traditional, dividend, sector, shadow, forensic, reporting |
| Backend: State schema (`state.py`) | DONE | Full AgentState TypedDict |
| Backend: DB manager (`db_manager.py`) | DONE | asyncpg, user_profiles, agent_memory_ltm, social_shares |
| Backend: Logger util (`logger.py`) | DONE | |
| Frontend: React 19 + Vite scaffold | DONE | `App.jsx`, `index.css`, `main.jsx` |
| Frontend: Auth flow (Google OAuth + bypass) | DONE | Matches Pledge Rover pattern |
| Frontend: Sidebar navigation | DONE | Dynamic — locks to profile if persona not set |
| Frontend: Intelligence Hub (dashboard tab) | DONE | Ticker input → /api/analyze → LangGraph |
| Frontend: Investor Profile (Sleep Test) | DONE | 3-step quiz → /api/profile/analyze |
| Frontend: Forecast Tracker tab | DONE | /api/forecasts/{handle} |

---

## Phase 2 — Infrastructure (COMPLETE — added this session)

| Item | Status | Notes |
|------|--------|-------|
| `market_rover/Dockerfile` | DONE | Multi-stage: React build + FastAPI. Mirrors Pledge Rover pattern |
| `market_rover/docker-compose.yml` | DONE | backend + frontend + postgres services |
| `market_rover/backend/.env.example` | DONE | All required env vars documented |
| `market_rover/frontend/.env.example` | DONE | VITE prefix vars |
| `market_rover/frontend/nginx.conf` | DONE | SPA routing + /api proxy to backend |
| `market_rover/frontend/vite.config.js` | UPDATED | Added /api proxy for local dev |
| `market_rover/backend/src/config/database.py` | DONE | Cloud SQL + local asyncpg pool |
| `market_rover/backend/src/routes/__init__.py` | DONE | Router extracted from server.py |
| `.github/workflows/market_rover_deploy.yml` | DONE | Mirrors investbrand_deploy.yml pattern |

---

## Phase 3 — Feature Completion (PENDING)

| Item | Status | Notes |
|------|--------|-------|
| Frontend: Shadow Discovery tab real data wiring | PENDING | Currently reads from forecast data — needs dedicated /api/shadow endpoint |
| Frontend: Trading Calendar tab | PENDING | Static content — needs /api/calendar endpoint pulling traditional_insights |
| Frontend: Portfolio Analysis tab | PENDING | Full portfolio input + batch /api/analyze with multiple tickers |
| Frontend: Market Heatmap tab | PENDING | Monthly returns heatmap — needs /api/heatmap/{ticker} endpoint |
| Backend: `/api/shadow` route | PENDING | Extract shadow_signals from agent_memory_ltm |
| Backend: `/api/calendar` route | PENDING | Expose traditional_insights from LangGraph |
| Backend: `/api/heatmap/{ticker}` route | PENDING | yfinance-based monthly returns matrix |
| Backend: Tests | PENDING | Mirror pledge_rover/backend test structure |
| DB schema migrations | PENDING | SQL migration file needed for prod Cloud SQL |
| Favicon / branding assets | PENDING | `market_rover/frontend/public/favicon.svg` |

---

## Cloud Run Target Services

| Service | Name | URL (post-deploy) |
|---------|------|-------------------|
| Backend API | `market-rover-api` | `https://market-rover-api-9514347926.us-central1.run.app` |
| Frontend UI | `market-rover-ui` | `https://market-rover-ui-9514347926.us-central1.run.app` |

Cloud SQL Instance: `market-rover:us-central1:investcraft-db` (shared instance — already exists)

---

## Local Dev Quick Start

```bash
# Backend
cd market_rover/backend
pip install -r requirements.txt
cp .env.example .env   # fill in GOOGLE_API_KEY
uvicorn src.server:app --reload --port 8080

# Frontend (separate terminal)
cd market_rover/frontend
npm install
cp .env.example .env
npm run dev            # http://localhost:3000
```

Or with Docker:
```bash
cd market_rover
docker-compose up --build
```

---

## Architectural Reference

```
market_rover/
├── Dockerfile                    # Multi-stage: React build + FastAPI (Cloud Run)
├── docker-compose.yml            # Local dev: backend + frontend + postgres
├── MIGRATION_STATUS.md           # This file
├── backend/
│   ├── .env.example
│   ├── requirements.txt
│   └── src/
│       ├── server.py             # FastAPI entrypoint + all route definitions
│       ├── state.py              # AgentState TypedDict (LangGraph)
│       ├── market_rover_graph.py # 10-node parallel LangGraph
│       ├── agents/               # 10 agent nodes (async)
│       ├── config/
│       │   └── database.py       # asyncpg pool (Cloud SQL + local)
│       ├── routes/               # Modular routers (extracted from server.py)
│       └── utils/
│           ├── db_manager.py
│           └── logger.py
└── frontend/
    ├── .env.example
    ├── nginx.conf                # SPA routing + /api proxy
    ├── vite.config.js            # /api proxy for local dev
    └── src/
        ├── App.jsx               # Single-file app (tabs: dashboard, profile, shadow, forecasts, calendar)
        ├── index.css             # Dark glassmorphism design system
        └── main.jsx
```
