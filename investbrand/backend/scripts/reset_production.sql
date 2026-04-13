-- InvestBrand: Production Clean-up & Fresh Start Logic
-- Targeted for Tamil New Year (April 14, 2026)

BEGIN;

-- 1. Purge all history/participation tables
-- CASCADE ensures any foreign key relationships are handled
TRUNCATE
    game_sessions,
    puzzle_votes,
    share_clicks,
    user_missions,
    user_strategy_tags,
    user_content_views,
    user_personas
CASCADE;

-- 2. Reset user profile metrics to baseline
UPDATE users SET
    total_score = 0,
    best_score = 0,
    streak = 0,
    last_played = NULL;

-- 3. Reset the Puzzle rotation
-- By setting scheduled_date to NULL, the new selection engine will
-- pick the FIRST community-voted winner tomorrow morning.
UPDATE puzzles SET
    scheduled_date = NULL,
    selection_method = 'lucky_draw';

COMMIT;

SELECT 'InvestBrand Hard-Reset Complete. Ready for Fresh Start.' as status;
