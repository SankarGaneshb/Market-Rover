-- Market-Rover v5.0 — PostgreSQL Schema Migrations
-- Cloud SQL instance: market-rover:us-central1:market-rover-db
-- Database: market_rover
-- Run order: top to bottom (all statements are idempotent via IF NOT EXISTS / ON CONFLICT)
-- Apply via: psql $DATABASE_URL -f schema.sql

SET client_encoding = 'UTF8';

-- ── User Profiles ──────────────────────────────────────────────────────────────
-- Stores investor persona (Hunter / Defender / Compounder / Preserver)
-- Written by: POST /api/profile and /api/profile/analyze
-- Read by:    GET  /api/profile/{user_handle}
CREATE TABLE IF NOT EXISTS public.user_profiles (
    user_id        TEXT PRIMARY KEY,
    persona        TEXT NOT NULL DEFAULT 'Not Set',
    last_updated   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ── Agent Long-Term Memory (LTM) ───────────────────────────────────────────────
-- Written by: reporting_node (after every /api/analyze run)
-- Read by:    retrieval_node, GET /api/forecasts, GET /api/shadow
CREATE TABLE IF NOT EXISTS public.agent_memory_ltm (
    id             BIGSERIAL PRIMARY KEY,
    user_id        TEXT NOT NULL,
    ticker         TEXT NOT NULL,
    stance         TEXT NOT NULL,           -- ACCUMULATION | DISTRIBUTION | WARNING | NEUTRAL
    logic_summary  TEXT,
    analysis_date  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, ticker)
);

-- Index for fast per-user and per-stance queries
CREATE INDEX IF NOT EXISTS idx_ltm_user     ON public.agent_memory_ltm (user_id);
CREATE INDEX IF NOT EXISTS idx_ltm_stance   ON public.agent_memory_ltm (stance);
CREATE INDEX IF NOT EXISTS idx_ltm_date     ON public.agent_memory_ltm (analysis_date DESC);

-- ── User Activity Log ──────────────────────────────────────────────────────────
-- Written by: reporting_node and any auth callback
-- Used by: future HIL analytics dashboard
CREATE TABLE IF NOT EXISTS public.user_activity_log (
    id             BIGSERIAL PRIMARY KEY,
    user_id        TEXT NOT NULL,
    action_type    TEXT NOT NULL,           -- GENERATED_INTEL_REPORT | LOGIN | etc.
    platform       TEXT NOT NULL DEFAULT 'WEB',
    created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_activity_user ON public.user_activity_log (user_id);
CREATE INDEX IF NOT EXISTS idx_activity_date ON public.user_activity_log (created_at DESC);

-- ── Social Shares ──────────────────────────────────────────────────────────────
-- Written by: db_manager.record_share (future share-button feature)
CREATE TABLE IF NOT EXISTS public.social_shares (
    id               BIGSERIAL PRIMARY KEY,
    user_id          TEXT NOT NULL,
    platform         TEXT NOT NULL,         -- WHATSAPP | X | LINKEDIN | etc.
    content_type     TEXT NOT NULL,
    recipient_count  INT NOT NULL DEFAULT 1,
    shared_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ── Verification Queries ───────────────────────────────────────────────────────
-- Run after apply to confirm schema is healthy
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
