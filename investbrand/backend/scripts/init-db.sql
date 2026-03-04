-- InvestCraft Database Schema for Cloud SQL PostgreSQL
-- Project: market-rover

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    google_id VARCHAR(255) UNIQUE NOT NULL,
    profile_picture TEXT,
    total_score INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- User streaks table
CREATE TABLE IF NOT EXISTS user_streaks (
    user_id UUID PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    last_played_date DATE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Game sessions table
CREATE TABLE IF NOT EXISTS game_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    brand_id INTEGER NOT NULL,
    brand_name VARCHAR(100) NOT NULL,
    company_name VARCHAR(100) NOT NULL,
    ticker_symbol VARCHAR(20) NOT NULL,
    difficulty VARCHAR(20) NOT NULL CHECK (difficulty IN ('easy', 'medium', 'hard')),
    score INTEGER NOT NULL CHECK (score >= 0),
    time_seconds INTEGER NOT NULL CHECK (time_seconds >= 0),
    moves_count INTEGER NOT NULL CHECK (moves_count >= 0),
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_game_sessions_user ON game_sessions(user_id, completed_at DESC);
CREATE INDEX IF NOT EXISTS idx_game_sessions_score ON game_sessions(score DESC, time_seconds ASC);

-- Daily challenges table
CREATE TABLE IF NOT EXISTS daily_challenges (
    challenge_date DATE PRIMARY KEY,
    brand_id INTEGER NOT NULL,
    brand_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User achievements table
CREATE TABLE IF NOT EXISTS user_achievements (
    achievement_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    achievement_type VARCHAR(50) NOT NULL,
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, achievement_type)
);

CREATE INDEX IF NOT EXISTS idx_achievements_user ON user_achievements(user_id);

-- Global leaderboard materialized view
CREATE MATERIALIZED VIEW IF NOT EXISTS global_leaderboard AS
SELECT
    gs.session_id,
    gs.user_id,
    u.username,
    u.profile_picture,
    gs.brand_name,
    gs.company_name,
    gs.difficulty,
    gs.score,
    gs.time_seconds,
    gs.moves_count,
    gs.completed_at,
    ROW_NUMBER() OVER (ORDER BY gs.score DESC, gs.time_seconds ASC) as rank
FROM game_sessions gs
JOIN users u ON gs.user_id = u.user_id
ORDER BY gs.score DESC, gs.time_seconds ASC
LIMIT 100;

CREATE UNIQUE INDEX IF NOT EXISTS idx_leaderboard_session ON global_leaderboard(session_id);
CREATE INDEX IF NOT EXISTS idx_leaderboard_rank ON global_leaderboard(rank);
CREATE INDEX IF NOT EXISTS idx_leaderboard_user ON global_leaderboard(user_id);

-- Function to update user streak
CREATE OR REPLACE FUNCTION update_user_streak(p_user_id UUID, p_play_date DATE)
RETURNS TABLE(current_streak INTEGER, longest_streak INTEGER) AS $$
DECLARE
    v_last_played DATE;
    v_current_streak INTEGER;
    v_longest_streak INTEGER;
BEGIN
    SELECT last_played_date, user_streaks.current_streak, user_streaks.longest_streak
    INTO v_last_played, v_current_streak, v_longest_streak
    FROM user_streaks WHERE user_id = p_user_id;

    IF NOT FOUND THEN
        INSERT INTO user_streaks (user_id, current_streak, longest_streak, last_played_date)
        VALUES (p_user_id, 1, 1, p_play_date);
        RETURN QUERY SELECT 1, 1;
        RETURN;
    END IF;

    IF v_last_played = p_play_date THEN
        RETURN QUERY SELECT v_current_streak, v_longest_streak;
        RETURN;
    END IF;

    IF v_last_played = p_play_date - INTERVAL '1 day' THEN
        v_current_streak := v_current_streak + 1;
    ELSE
        v_current_streak := 1;
    END IF;

    IF v_current_streak > v_longest_streak THEN
        v_longest_streak := v_current_streak;
    END IF;

    UPDATE user_streaks
    SET current_streak = v_current_streak,
        longest_streak = v_longest_streak,
        last_played_date = p_play_date,
        updated_at = CURRENT_TIMESTAMP
    WHERE user_id = p_user_id;

    RETURN QUERY SELECT v_current_streak, v_longest_streak;
END;
$$ LANGUAGE plpgsql;

-- Auto-update updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
