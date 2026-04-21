-- Market_Rover v5 Initialization Script
-- Provisioned for Cloud SQL Synchronization

CREATE SCHEMA IF NOT EXISTS "Market_Rover";

-- User Profiles
CREATE TABLE IF NOT EXISTS public.user_profiles (
    user_id TEXT PRIMARY KEY,
    persona TEXT DEFAULT 'Neutral',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent Memory Long Term Storage (LTM)
CREATE TABLE IF NOT EXISTS public.agent_memory_ltm (
    user_id TEXT,
    ticker TEXT,
    stance TEXT,
    logic_summary TEXT,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, ticker)
);

-- Social Shares Logging
CREATE TABLE IF NOT EXISTS public.social_shares (
    id SERIAL PRIMARY KEY,
    user_id TEXT,
    platform TEXT,
    content_type TEXT,
    recipient_count INT DEFAULT 1,
    shared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Activity Logs
CREATE TABLE IF NOT EXISTS public.user_activity_log (
    id SERIAL PRIMARY KEY,
    user_id TEXT,
    action_type TEXT,
    platform TEXT,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
