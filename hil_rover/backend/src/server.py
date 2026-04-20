from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import uuid
import time
from datetime import datetime, timezone, timedelta
import asyncpg
import json
import httpx

# HIL-Rover Version: 4.4.0 — PostgreSQL persistence + GitHub Reactor

# HIL-Rover Version: 4.3.0 — PostgreSQL persistence (investbrand-db:hil_rover)
app = FastAPI(title="HIL Rover API")

DIST_PATH = os.environ.get("HIL_FRONTEND_PATH", "../frontend/dist")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Database pool ──────────────────────────────────────────────────────────────

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await _create_pool()
    return _pool


async def _create_pool() -> asyncpg.Pool:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        conn_name = os.getenv("CLOUD_SQL_CONNECTION_NAME", "")
        db_user   = os.getenv("PR_DB_USER", os.getenv("DB_USER", "postgres"))
        db_pass   = os.getenv("PR_DB_PASSWORD", os.getenv("DB_PASSWORD", ""))
        db_name   = os.getenv("HIL_DB_NAME", "hil_rover")
        if conn_name:
            socket_dir = f"/cloudsql/{conn_name}"
            database_url = f"postgresql://{db_user}:{db_pass}@/{db_name}?host={socket_dir}"

        else:
            # local dev fallback
            database_url = f"postgresql://{db_user}:{db_pass}@localhost:5432/{db_name}"
    pool = await asyncpg.create_pool(dsn=database_url, min_size=1, max_size=5)
    # Ensure schema exists
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS hil_requests (
                id           TEXT PRIMARY KEY,
                agent_name   TEXT NOT NULL,
                task_name    TEXT NOT NULL,
                instructions TEXT,
                status       TEXT NOT NULL DEFAULT 'PENDING',
                decision     TEXT,
                comments     TEXT,
                data         JSONB,
                created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                processed_at TIMESTAMPTZ
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_hil_status  ON hil_requests (status)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_hil_created ON hil_requests (created_at DESC)")
    print("[HIL] Database pool ready.")
    return pool


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


@app.on_event("startup")
async def on_startup():
    print("[HIL] Mission Control starting up...")
    # Pool will be initialized lazily on first request to avoid blocking port bind



@app.on_event("shutdown")
async def on_shutdown():
    await close_pool()

# ── Data helpers ───────────────────────────────────────────────────────────────


def _row_to_dict(r: asyncpg.Record) -> dict:
    d = dict(r)
    if d.get("created_at"):
        d["created_at"] = d["created_at"].isoformat()
    if d.get("processed_at"):
        d["processed_at"] = d["processed_at"].isoformat()
    if isinstance(d.get("data"), str):
        try:
            d["data"] = json.loads(d["data"])
        except Exception:
            pass
    return d

# ── Models ─────────────────────────────────────────────────────────────────────


class HILDecision(BaseModel):
    decision: str
    comments: Optional[str] = None

# ── SRE audit ─────────────────────────────────────────────────────────────────


# from scripts.sre_sentinel import run_sre_sentinel (Moved to handler)



@app.post("/api/sre/audit")
async def trigger_sre_audit():
    try:
        from scripts.sre_sentinel import run_sre_sentinel
        run_sre_sentinel()
        return {"status": "Audit successful", "message": "SRE Support has scanned the infrastructure."}

    except Exception as e:
        return {"status": "Error", "message": str(e)}


# ── Infrastructure provisioning ────────────────────────────────────────────────

# Market Rover DDL — mirrors market_rover/backend/src/config/schema.sql
_MARKET_ROVER_DDL = """
CREATE TABLE IF NOT EXISTS public.user_profiles (
    user_id      TEXT PRIMARY KEY,
    persona      TEXT DEFAULT 'Neutral',
    last_updated TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS public.agent_memory_ltm (
    id            SERIAL PRIMARY KEY,
    user_id       TEXT NOT NULL,
    ticker        TEXT NOT NULL,
    stance        TEXT NOT NULL,
    logic_summary TEXT,
    analysis_date TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, ticker)
);
CREATE TABLE IF NOT EXISTS public.user_activity_log (
    id          SERIAL PRIMARY KEY,
    user_id     TEXT NOT NULL,
    action_type TEXT NOT NULL,
    platform    TEXT DEFAULT 'WEB',
    logged_at   TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS public.social_shares (
    id               SERIAL PRIMARY KEY,
    user_id          TEXT NOT NULL,
    platform         TEXT NOT NULL,
    content_type     TEXT NOT NULL,
    recipient_count  INTEGER DEFAULT 1,
    shared_at        TIMESTAMPTZ DEFAULT NOW()
);
"""

# HIL Rover DDL — mirrors hil_rover/backend/src/hil_schema.sql
_HIL_DDL = """
CREATE TABLE IF NOT EXISTS hil_requests (
    id           TEXT PRIMARY KEY,
    agent_name   TEXT NOT NULL,
    task_name    TEXT NOT NULL,
    instructions TEXT,
    status       TEXT NOT NULL DEFAULT 'PENDING',
    decision     TEXT,
    comments     TEXT,
    data         JSONB,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_hil_status  ON hil_requests (status);
CREATE INDEX IF NOT EXISTS idx_hil_created ON hil_requests (created_at DESC);
"""


def _build_dsn(db_name: str) -> str:
    """Build a DSN for a specific database on the shared investbrand-db instance."""
    conn_name = os.getenv("CLOUD_SQL_CONNECTION_NAME", "")
    db_user   = os.getenv("DB_USER", "postgres")
    db_pass   = os.getenv("DB_PASSWORD", "")
    if conn_name:
        socket = f"/cloudsql/{conn_name}/.s.PGSQL.5432"
        return f"postgresql://{db_user}:{db_pass}@/{db_name}?host={socket}"
    return f"postgresql://{db_user}:{db_pass}@localhost:5432/{db_name}"


@app.post("/api/provision")
async def provision_infrastructure():
    """
    Creates all 3 missing databases on the shared investbrand-db Cloud SQL instance
    and applies the Market Rover + HIL Rover schemas. Fully idempotent.
    """
    log = []
    errors = []

    # Step 1: CREATE databases via the 'postgres' system database
    # CREATE DATABASE cannot run inside a transaction — use autocommit
    target_dbs = ["market_rover", "pledge_rover", "hil_rover"]
    try:
        sys_conn = await asyncpg.connect(dsn=_build_dsn("postgres"))
        await sys_conn.execute("SET client_encoding TO 'UTF8'")
        for db in target_dbs:
            exists = await sys_conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1", db
            )
            if exists:
                log.append(f"DB '{db}' already exists — skipped.")
            else:
                # Must run outside transaction block
                await sys_conn.execute(f'CREATE DATABASE "{db}"')
                log.append(f"DB '{db}' created.")
        await sys_conn.close()
    except Exception as e:
        errors.append(f"DB creation error: {e}")

    # Step 2: Apply Market Rover schema on market_rover DB
    try:
        conn = await asyncpg.connect(dsn=_build_dsn("market_rover"))
        await conn.execute(_MARKET_ROVER_DDL)
        await conn.close()
        log.append("Market Rover schema applied to 'market_rover'.")
    except Exception as e:
        errors.append(f"Market Rover schema error: {e}")

    # Step 3: Apply HIL schema on hil_rover DB
    try:
        conn = await asyncpg.connect(dsn=_build_dsn("hil_rover"))
        await conn.execute(_HIL_DDL)
        await conn.close()
        log.append("HIL Rover schema applied to 'hil_rover'.")
    except Exception as e:
        errors.append(f"HIL Rover schema error: {e}")

    # Pledge Rover auto-migrates on first startup — no manual DDL needed.
    log.append("Pledge Rover: auto-migration on first deployment startup.")

    return {
        "status": "done" if not errors else "partial",
        "log": log,
        "errors": errors,
    }


# ── Static stat endpoints (no DB needed) ──────────────────────────────────────


@app.get("/api/health-stats")
async def get_health_stats():
    return {
        "api_latency": "142ms",
        "cache_hit_rate": "84.2%",
        "token_usage_total": "1.2M",
        "active_crews": 2,
        "error_rate": "0.04%"
    }


@app.get("/api/brain-manifest")
async def get_brain_manifest():
    return {
        "agents": [
            {"name": "Portfolio Manager",  "role": "Portfolio Processing",   "platform": "Market-Rover",  "status": "Active"},
            {"name": "Market Strategist",  "role": "Macro & News",            "platform": "Market-Rover",  "status": "Active"},
            {"name": "Sentiment Expert",   "role": "Psychological Edge",      "platform": "Market-Rover",  "status": "Active"},
            {"name": "Technical Analyst",  "role": "Price Action",            "platform": "Market-Rover",  "status": "Active"},
            {"name": "Report Writer",      "role": "Intelligence Sync",       "platform": "Market-Rover",  "status": "Active"},
            {"name": "Data Visualizer",    "role": "Graphing Engine",         "platform": "Market-Rover",  "status": "Active"},
            {"name": "Shadow Analyst",     "role": "Institutional Flow",      "platform": "Market-Rover",  "status": "Analyzing NSE"},
            {"name": "Timing Analyst",     "role": "Contextual Timing",       "platform": "Market-Rover",  "status": "Active"},
            {"name": "Game Master",        "role": "Puzzle Orchestration",    "platform": "InvestBrand",   "status": "Active"},
            {"name": "Brand Profiler",     "role": "Entity Mapping",          "platform": "InvestBrand",   "status": "Active"},
            {"name": "Teacher Agent",      "role": "Financial Literacy",      "platform": "InvestBrand",   "status": "Active"},
            {"name": "QC Agent",           "role": "Asset Validation",        "platform": "InvestBrand",   "status": "Active"},
            {"name": "Ops Support SRE",    "role": "Runtime & Dependency Governance", "platform": "InvestBrand",   "status": "Active"},
            {"name": "Pledge Council",     "role": "Risk Assessment",         "platform": "Pledge Rover",  "status": "Active"},
            {"name": "Data Harvester",     "role": "BSE/NSE Scraping",        "platform": "Pledge Rover",  "status": "Active"},
        ]
    }


@app.get("/api/kpi-leaderboard")
async def get_kpi_leaderboard():
    pool = await get_pool()
    sre_score = 98
    sre_status = "Optimal"

    async with pool.acquire() as conn:
        # Calculate TTR for SRE Support tasks (requests created and processed)
        # Target is <= 1 hour (3600 seconds)
        stats = await conn.fetchrow("""
            SELECT
                AVG(EXTRACT(EPOCH FROM (processed_at - created_at))) FILTER (WHERE processed_at IS NOT NULL) as avg_ttr_secs,
                COUNT(*) FILTER (WHERE status = 'PENDING' AND created_at < NOW() - INTERVAL '1 hour') as overdue_count
            FROM hil_requests
            WHERE agent_name = 'SRE Support'
        """)

        if stats:
            avg_ttr = stats["avg_ttr_secs"] or 0
            overdue = stats["overdue_count"] or 0

            # Penalty for high average TTR (> 1 hour)
            if avg_ttr > 3600:
                sre_score -= min(30, int((avg_ttr - 3600) / 600)) # -1 point for every 10 mins over

            # Massive penalty for currently unresolved build failures exceeding 1 hour
            if overdue > 0:
                sre_score -= (overdue * 15)

            sre_score = max(0, sre_score)

            if sre_score < 60: sre_status = "Critical"
            elif sre_score < 85: sre_status = "Warning"
            elif sre_score < 95: sre_status = "Near Target"

    return [
        {"agent": "Strategist",    "kpi": "Funnel Integrity",   "score": 94, "target": 90, "status": "Above Target"},
        {"agent": "Shadow Analyst","kpi": "Divergence Alpha",    "score": 82, "target": 70, "status": "Above Target"},
        {"agent": "Market Context","kpi": "Technical Precision", "score": 78, "target": 80, "status": "Near Target"},
        {"agent": "SRE Support",   "kpi": "SLA Governance",      "score": sre_score, "target": 95, "status": sre_status},
    ]

# ── HIL Request queue (PostgreSQL-backed) ──────────────────────────────────────


@app.get("/api/requests")
async def get_all_requests():
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM hil_requests ORDER BY created_at DESC")
    return [_row_to_dict(r) for r in rows]


@app.post("/api/requests")
async def create_request(request: Request):
    try:
        data = await request.json()
        if not data.get("agent_name") or not data.get("task_name"):
            return JSONResponse(status_code=400, content={"error": "Missing agent_name or task_name"})

        req_id     = data.get("id") or f"EXT-{int(time.time())}"
        status     = data.get("status") or "PENDING"
        created_at = datetime.now(timezone.utc)
        raw_data   = json.dumps(data.get("data")) if data.get("data") else None

        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO hil_requests
                    (id, agent_name, task_name, instructions, status, data, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (id) DO UPDATE SET
                    status = EXCLUDED.status,
                    instructions = EXCLUDED.instructions
            """, req_id, data["agent_name"], data["task_name"],
                data.get("instructions"), status, raw_data, created_at)

        return {"status": "success", "id": req_id}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/requests/{request_id}/process")
async def process_request(request_id: str, decision: HILDecision):
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("""
            UPDATE hil_requests
            SET status       = $1,
                decision     = $1,
                comments     = $2,
                processed_at = NOW()
            WHERE id = $3
        """, decision.decision, decision.comments, request_id)
        if result == "UPDATE 0":
            raise HTTPException(status_code=404, detail="Request not found")

        # REACTIVE ENGINE: If approved, execute the corresponding agentic action
        if decision.decision == "APPROVED":
            # Fetch request details to check for Handovers
            req = await conn.fetchrow("SELECT * FROM hil_requests WHERE id = $1", request_id)
            if req and "Dependency Guard" in req["agent_name"]:
                await _handle_dependabot_merge(req)

    return {"status": "success"}


async def _handle_dependabot_merge(req: asyncpg.Record):
    """
    Hands over the approved dependency update to the SRE Agent's automated merge engine.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("[HIL REACTOR] Error: GITHUB_TOKEN not set. Cannot merge PR.")
        return

    try:
        data = json.loads(req["data"]) if isinstance(req["data"], str) else req["data"]
        pr_url = data.get("pr_url")
        if not pr_url:
            return

        # Extract repo and PR number (e.g., https://github.com/user/repo/pull/123)
        parts = pr_url.split("/")
        owner = parts[-4]
        repo  = parts[-3]
        pr_num = parts[-1]

        print(f"[HIL REACTOR] SRE Agent initiating merge for {owner}/{repo} PR #{pr_num}...")

        async with httpx.AsyncClient() as client:
            merge_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}/merge"
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            # We use 'squash' as default for clean history
            resp = await client.put(merge_url, headers=headers, json={
                "merge_method": "squash",
                "commit_title": f"HIL APPROVED: {req['task_name']}",
                "commit_message": f"Human-In-The-Loop approval granted via Mission Control. Comments: {req.get('comments', 'None')}"
            })

            if resp.status_code == 200:
                print(f"[HIL REACTOR] Successfully merged PR #{pr_num}.")
            else:
                print(f"[HIL REACTOR] Failed to merge PR #{pr_num}: {resp.text}")

    except Exception as e:
        print(f"[HIL REACTOR] Unexpected error during merge handover: {e}")


@app.get("/api/stats")
async def get_stats():
    pool = await get_pool()
    async with pool.acquire() as conn:
        totals = await conn.fetchrow("""
            SELECT
                COUNT(*)                                            AS total,
                COUNT(*) FILTER (WHERE status = 'APPROVED')        AS approved,
                COUNT(*) FILTER (WHERE status = 'REJECTED')        AS rejected,
                COUNT(*) FILTER (WHERE status = 'PENDING')         AS pending,
                COUNT(*) FILTER (
                    WHERE status = 'PENDING'
                    AND created_at < NOW() - INTERVAL '24 hours'
                )                                                   AS sla_breaches
            FROM hil_requests
        """)
    total    = totals["total"]
    approved = totals["approved"]
    rejected = totals["rejected"]
    combined = approved + rejected
    return {
        "total":         total,
        "approved":      approved,
        "rejected":      rejected,
        "pending":       totals["pending"],
        "sla_breaches":  totals["sla_breaches"],
        "approval_rate": (approved / combined * 100) if combined > 0 else 0,
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}

# ── Static assets + SPA catch-all ─────────────────────────────────────────────

if os.path.exists(os.path.join(DIST_PATH, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST_PATH, "assets")), name="assets")


@app.get("/{path:path}")
async def catch_all(path: str):
    index_file = os.path.join(DIST_PATH, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"status": "Mission Control initializing... please refresh in 10s"}
