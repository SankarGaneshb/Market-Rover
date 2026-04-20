-- HIL Rover — PostgreSQL Schema
-- Database: hil_rover  (on shared instance: market-rover:us-central1:market-rover-db)
-- Apply via:  psql -h 127.0.0.1 -U postgres -d hil_rover -f hil_schema.sql

SET client_encoding = 'UTF8';

-- HIL request queue — replaces the /app/data/hil_requests.json flat file
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
