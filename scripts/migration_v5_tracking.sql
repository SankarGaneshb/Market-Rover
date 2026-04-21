-- Market-Rover Evolution: Tracking & Memory Migration
-- Date: 2026-04-15

-- 1. User Login & Session Tracking
CREATE TABLE IF NOT EXISTS public.user_activity_log (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    action_type VARCHAR(50) NOT NULL, -- LOGIN, LOGOUT, PAGE_VIEW
    session_id VARCHAR(255),
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Social Engagement (Viral Loop Tracking)
CREATE TABLE IF NOT EXISTS public.social_shares (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    platform VARCHAR(50) NOT NULL, -- WHATSAPP, X, LINKEDIN, TELEGRAM
    content_type VARCHAR(50) NOT NULL, -- PORTFOLIO_REPORT, GAME_SCORE, APP_INVITE
    content_id VARCHAR(255), -- ID of the report or game session
    recipient_count INTEGER DEFAULT 1,
    share_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Long-Term Agent Memory (LTM)
CREATE TABLE IF NOT EXISTS public.agent_memory_ltm (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    stance VARCHAR(50) NOT NULL, -- BULLISH, BEARISH, NEUTRAL
    logic_summary TEXT, -- The 'why' behind the last analysis
    final_report_ref VARCHAR(255), -- Link to storage/report_id
    analysis_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB -- Flexible storage for indicators at time of analysis
);

-- Indexing for performance
CREATE INDEX IF NOT EXISTS idx_user_activity_user ON public.user_activity_log(user_id);
CREATE INDEX IF NOT EXISTS idx_social_shares_user ON public.social_shares(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_memory_ticker ON public.agent_memory_ltm(ticker);

COMMENT ON TABLE public.user_activity_log IS 'Tracks user login history and interaction points for SRE auditing.';
COMMENT ON TABLE public.social_shares IS 'Tracks viral loops and how users are sharing Market-Rover content.';
COMMENT ON TABLE public.agent_memory_ltm IS 'Provides a "Brain" for agents to recall past analysis and avoid repetitive logic.';
