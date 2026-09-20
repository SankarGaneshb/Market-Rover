"""
InvestBrand Native FastAPI Router
Consolidates InvestBrand gamified investing puzzles, community voting,
leaderboards, missions, and AI-driven market intelligence for the Market-Rover Unified Gateway.
"""
import os
import json
import logging
import asyncio
import hashlib
from datetime import datetime, date, timezone, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Request, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger("market_rover.investbrand")

router = APIRouter(tags=["investbrand"])

# ── Load embedded brands data ──────────────────────────────────────────────────
BRANDS_FILE = Path(__file__).resolve().parent / "brands_data.json"
NIFTY50_BRANDS: List[Dict[str, Any]] = []

if BRANDS_FILE.exists():
    try:
        with open(BRANDS_FILE, "r", encoding="utf-8") as f:
            NIFTY50_BRANDS = json.load(f)
        logger.info(f"[InvestBrand] Loaded {len(NIFTY50_BRANDS)} brands from brands_data.json")
    except Exception as e:
        logger.warning(f"[InvestBrand] Error reading brands_data.json: {e}")

if not NIFTY50_BRANDS:
    # Minimal embedded fallback if file missing
    NIFTY50_BRANDS = [
        {"id": 1, "brand": "Jio", "company": "Reliance Industries", "ticker": "RELIANCE", "sector": "Energy", "insight": "Digital powerhouse revolutionizing 4G/5G.", "logoSvg": "<svg viewBox='0 0 400 400'><rect width='400' height='400' fill='#0057FF'/><text x='200' y='220' fill='white' font-size='80' text-anchor='middle'>Jio</text></svg>"},
        {"id": 2, "brand": "TCS", "company": "Tata Consultancy Services", "ticker": "TCS", "sector": "IT", "insight": "Pioneered India's IT export boom.", "logoSvg": "<svg viewBox='0 0 400 400'><rect width='400' height='400' fill='#002D72'/><text x='200' y='220' fill='white' font-size='80' text-anchor='middle'>TCS</text></svg>"},
        {"id": 3, "brand": "HDFC Bank", "company": "HDFC Bank", "ticker": "HDFCBANK", "sector": "Financials", "insight": "India's premier private banking institution.", "logoSvg": "<svg viewBox='0 0 400 400'><rect width='400' height='400' fill='#004C8F'/><text x='200' y='220' fill='white' font-size='60' text-anchor='middle'>HDFC</text></svg>"},
        {"id": 4, "brand": "Infosys", "company": "Infosys", "ticker": "INFY", "sector": "IT", "insight": "Global leader in digital consulting and software.", "logoSvg": "<svg viewBox='0 0 400 400'><rect width='400' height='400' fill='#007CC3'/><text x='200' y='220' fill='white' font-size='60' text-anchor='middle'>Infosys</text></svg>"},
        {"id": 5, "brand": "SBI", "company": "State Bank of India", "ticker": "SBIN", "sector": "Financials", "insight": "Largest public sector bank in India.", "logoSvg": "<svg viewBox='0 0 400 400'><rect width='400' height='400' fill='#1F4788'/><text x='200' y='220' fill='white' font-size='70' text-anchor='middle'>SBI</text></svg>"}
    ]

# ── Lazy-loaded Database Connection Pool (GoA Rule #1) ────────────────────────
_pool = None
_pool_lock = asyncio.Lock()

async def get_db_pool():
    global _pool
    if _pool is not None:
        return _pool

    async with _pool_lock:
        if _pool is not None:
            return _pool
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            return None
        try:
            import asyncpg
            logger.info("[InvestBrand] Connecting to PostgreSQL pool...")
            _pool = await asyncpg.create_pool(
                dsn=database_url,
                min_size=1,
                max_size=5,
                command_timeout=10
            )
            # Create essential tables if not exist
            async with _pool.acquire() as conn:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS public.investbrand_users (
                        id SERIAL PRIMARY KEY,
                        google_id VARCHAR(255) UNIQUE,
                        email VARCHAR(255) UNIQUE,
                        name VARCHAR(255) DEFAULT 'Player',
                        avatar_url TEXT,
                        streak INTEGER DEFAULT 0,
                        last_played DATE,
                        total_score INTEGER DEFAULT 0,
                        best_score INTEGER DEFAULT 0,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    CREATE TABLE IF NOT EXISTS public.investbrand_votes (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER,
                        brand_id INTEGER,
                        vote_date DATE NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    CREATE TABLE IF NOT EXISTS public.investbrand_sessions (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER,
                        puzzle_id INTEGER,
                        brand_id INTEGER,
                        score INTEGER DEFAULT 0,
                        difficulty VARCHAR(50) DEFAULT 'easy',
                        time_taken INTEGER DEFAULT 0,
                        solved_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """)
            logger.info("[InvestBrand] DB tables initialized successfully.")
            return _pool
        except Exception as e:
            logger.warning(f"[InvestBrand] Database connection failed ({e}). Using resilient fallback store.")
            return None

def get_ist_date() -> str:
    """Returns today's date string in IST (UTC+5:30)."""
    ist_now = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
    return ist_now.strftime("%Y-%m-%d")

def get_brand_by_id(brand_id: int) -> Optional[Dict[str, Any]]:
    for b in NIFTY50_BRANDS:
        if b.get("id") == brand_id:
            return b
    return None

def get_daily_brand(date_str: str) -> Dict[str, Any]:
    """Deterministically pick a brand for a given date."""
    h = int(hashlib.md5(date_str.encode("utf-8")).hexdigest(), 16)
    idx = h % len(NIFTY50_BRANDS)
    return NIFTY50_BRANDS[idx]


# ── Request / Response Models ─────────────────────────────────────────────────
class GuessPayload(BaseModel):
    guess: str

class CompletePayload(BaseModel):
    score: Optional[int] = 100
    difficulty: Optional[str] = "easy"
    time_taken: Optional[int] = 30
    attempts: Optional[int] = 1

class VotePayload(BaseModel):
    brandId: Optional[int] = None
    brand_id: Optional[int] = None

class TrackClickPayload(BaseModel):
    promoterId: Optional[int] = None
    ref: Optional[str] = "direct"

class SocialLoginPayload(BaseModel):
    token: Optional[str] = None
    provider: Optional[str] = "google"


# ── In-Memory State for Resilient Fallback ────────────────────────────────────
_MEMORY_VOTES: Dict[str, List[int]] = {}  # date_str -> list of brand_ids
_MEMORY_SESSIONS: List[Dict[str, Any]] = []


# ── Route Handlers ────────────────────────────────────────────────────────────

@router.get("/health")
@router.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "service": "InvestBrand Unified API",
        "version": "5.0.0",
        "timestamp": get_ist_date(),
        "total_brands": len(NIFTY50_BRANDS)
    }

@router.get("/puzzles/daily")
async def get_daily_puzzle(brand_id: Optional[int] = None, ticker: Optional[str] = None):
    """Fetch the active puzzle for today, supporting optional ticker/brand override for testing."""
    today = get_ist_date()
    pool = await get_db_pool()

    brand = None
    selection_method = "lucky_draw"

    # 1. Check if user requested a specific ticker or brand_id for testing
    if ticker:
        for b in NIFTY50_BRANDS:
            if b.get("ticker", "").upper() == ticker.upper() or b.get("brand", "").lower() == ticker.lower():
                brand = b
                selection_method = "featured_sample"
                break
    elif brand_id:
        brand = get_brand_by_id(brand_id)
        if brand:
            selection_method = "featured_sample"

    # 2. Check for community votes first if not overridden
    if not brand and pool:
        try:
            async with pool.acquire() as conn:
                vote_row = await conn.fetchrow(
                    "SELECT brand_id, COUNT(*) as cnt FROM public.investbrand_votes WHERE vote_date = $1 GROUP BY brand_id ORDER BY cnt DESC LIMIT 1",
                    date.fromisoformat(today)
                )
                if vote_row and vote_row["brand_id"]:
                    voted_id = vote_row["brand_id"]
                    brand = get_brand_by_id(voted_id)
                    if brand:
                        selection_method = "voted"
        except Exception as e:
            logger.warning(f"[InvestBrand] Error checking DB votes: {e}")

    # 3. Default to featured LICI sample (Brand #1) or daily rotation
    if not brand:
        brand = get_brand_by_id(1) or get_daily_brand(today)

    brand_id = brand.get("id", 1)
    return {
        "id": brand_id,
        "puzzle_date": today,
        "brand_id": brand_id,
        "brand_name": brand.get("brand", "LIC"),
        "company_name": brand.get("company", "Life Insurance Corporation of India"),
        "ticker": brand.get("ticker", "LICI"),
        "logo_url": brand.get("logoUrl", "/logos/LICI.png"),
        "logo_svg": brand.get("logoSvg", ""),
        "difficulty": 1,
        "sector": brand.get("sector", "Financials"),
        "hint": f"Leading brand in the {brand.get('sector', 'Financials')} sector.",
        "selection_method": selection_method,
        "scheduled_date": today,
        "total_votes": 0
    }

@router.get("/puzzles/{puzzle_id}/clues")
async def get_puzzle_clues(puzzle_id: int):
    """Progressive clues for solving the puzzle."""
    brand = get_brand_by_id(puzzle_id) or get_daily_brand(get_ist_date())
    sector = brand.get("sector", "Market")
    b_name = brand.get("brand", "")
    company = brand.get("company", "")
    ticker = brand.get("ticker", "")

    sector_clouds = {
        "Energy": "Refining, Jio, Petrochemicals, Oil, Solar, Cash Flow",
        "IT": "Software, Cloud, AI, Consulting, Digital, Global",
        "Financials": "Banking, Credit, Deposits, Wealth, Capital, Lending",
        "Consumer Goods": "FMCG, Brands, Retail, Distribution, Packaging, Household",
        "Automobile": "EV, Engines, Trucks, Passenger, Mobility, Assembly",
        "Pharma": "Healthcare, Formulations, API, Labs, Medicine, Biotech",
        "Metals": "Steel, Aluminium, Mining, Smelting, Infrastructure",
        "Telecom": "5G, Data, Towers, Bandwidth, Broadband, ARPU",
        "Power": "Thermal, Hydro, Grid, Renewable, Transmission"
    }
    word_cloud = sector_clouds.get(sector, "Growth, Value, Quality, Moat, Market Leader")

    clue1 = f"Sector Clue: Operating in the {sector} sector with significant Indian market presence."
    clue2 = f"Word Clue: {len(b_name)} letters, starts with '{b_name[0].upper() if b_name else '?'}'."
    clue3 = f"Stock Clue: Owned by {company} (Ticker: {ticker}), traded on the NSE/BSE."

    return {
        "success": True,
        "puzzle_id": puzzle_id,
        "clues": {
            "clue1": clue1,
            "clue2": clue2,
            "clue3": clue3,
            "wordCloud": word_cloud,
            "logoSvg": brand.get("logoSvg", ""),
            "logoUrl": brand.get("logoUrl", "")
        }
    }

@router.post("/puzzles/{puzzle_id}/guess")
async def evaluate_puzzle_guess(puzzle_id: int, payload: GuessPayload):
    """Validate user guess against brand, company name, or ticker."""
    brand = get_brand_by_id(puzzle_id) or get_daily_brand(get_ist_date())
    user_guess = payload.guess.strip().lower()

    target_brand = (brand.get("brand") or "").strip().lower()
    target_company = (brand.get("company") or "").strip().lower()
    target_ticker = (brand.get("ticker") or "").strip().lower()

    is_correct = (
        user_guess == target_brand or
        user_guess == target_company or
        user_guess == target_ticker or
        (len(user_guess) >= 3 and user_guess in target_brand)
    )

    if is_correct:
        msg = f"Spot on! You correctly identified {brand.get('brand')}."
        return {
            "success": True,
            "correct": True,
            "isCorrect": True,
            "brand": brand.get("brand"),
            "company": brand.get("company"),
            "ticker": brand.get("ticker"),
            "score": 100,
            "message": msg,
            "feedback": msg
        }
    else:
        msg = "Not quite! Try checking the sector and word clues again."
        return {
            "success": True,
            "correct": False,
            "isCorrect": False,
            "message": msg,
            "feedback": msg
        }

@router.post("/puzzles/{puzzle_id}/complete")
async def complete_puzzle(puzzle_id: int, payload: CompletePayload):
    """Record completed game and return updated streak and stats."""
    brand = get_brand_by_id(puzzle_id) or get_daily_brand(get_ist_date())
    today = get_ist_date()
    score = payload.score or 100

    pool = await get_db_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO public.investbrand_sessions (puzzle_id, brand_id, score, difficulty, time_taken)
                    VALUES ($1, $2, $3, $4, $5)
                """, puzzle_id, brand.get("id", 1), score, payload.difficulty, payload.time_taken)
        except Exception as e:
            logger.warning(f"[InvestBrand] Failed recording session to DB: {e}")

    _MEMORY_SESSIONS.append({
        "puzzle_id": puzzle_id,
        "brand_id": brand.get("id", 1),
        "score": score,
        "date": today
    })

    return {
        "success": True,
        "score": score,
        "xp_earned": score,
        "streak": max(1, len(_MEMORY_SESSIONS)),
        "total_score": sum(s.get("score", 0) for s in _MEMORY_SESSIONS),
        "level": "Junior Virtuoso"
    }

@router.get("/puzzles/{puzzle_id}/insight")
async def get_puzzle_insight(puzzle_id: int):
    """Fetch Teacher / Market Insight for the solved puzzle."""
    brand = get_brand_by_id(puzzle_id) or get_daily_brand(get_ist_date())
    insight = brand.get("insight") or f"{brand.get('brand')} is a prominent business under {brand.get('company')} ({brand.get('ticker')})."

    # Generate live Gemini AI explanation if GOOGLE_API_KEY is available
    ai_teacher_tip = None
    if os.getenv("GOOGLE_API_KEY"):
        try:
            from google import genai
            client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
            prompt = (
                f"In 2 concise sentences, provide an educational investing lesson on {brand.get('company')} ({brand.get('ticker')}) "
                f"and its brand '{brand.get('brand')}'. Explain why understanding customer brand loyalty helps stock investors."
            )
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            if resp and resp.text:
                ai_teacher_tip = resp.text.strip()
        except Exception as e:
            logger.debug(f"[InvestBrand] AI Insight generation exception: {e}")

    if not ai_teacher_tip:
        ai_teacher_tip = f"Investing in companies with strong brand recall like {brand.get('brand')} provides pricing power and defensible economic moats."

    return {
        "success": True,
        "brand": brand.get("brand"),
        "company": brand.get("company"),
        "ticker": brand.get("ticker"),
        "sector": brand.get("sector"),
        "insight": insight,
        "teacher_tip": ai_teacher_tip,
        "financial_concept": f"Brand Moat & {brand.get('sector')} Growth"
    }

@router.get("/puzzles/vote-status")
async def get_vote_status():
    """Return candidates for tomorrow's community vote."""
    today = get_ist_date()
    candidates = NIFTY50_BRANDS[:5]

    pool = await get_db_pool()
    votes_map = {}
    if pool:
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT brand_id, COUNT(*) as cnt FROM public.investbrand_votes WHERE vote_date = $1 GROUP BY brand_id",
                    date.fromisoformat(today) + timedelta(days=1)
                )
                for r in rows:
                    votes_map[r["brand_id"]] = r["cnt"]
        except Exception as e:
            logger.warning(f"[InvestBrand] Error fetching vote counts: {e}")

    candidate_list = []
    for c in candidates:
        b_id = c.get("id")
        candidate_list.append({
            "brand_id": b_id,
            "brand": c.get("brand"),
            "company": c.get("company"),
            "sector": c.get("sector"),
            "votes": votes_map.get(b_id, 0)
        })

    return {
        "has_voted": False,
        "candidates": candidate_list,
        "vote_date": (date.fromisoformat(today) + timedelta(days=1)).isoformat()
    }

@router.post("/puzzles/vote")
async def cast_vote(payload: VotePayload):
    """Cast a community vote for tomorrow's puzzle brand."""
    b_id = payload.brandId or payload.brand_id or 1
    today = get_ist_date()
    tomorrow = (date.fromisoformat(today) + timedelta(days=1)).isoformat()

    pool = await get_db_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO public.investbrand_votes (brand_id, vote_date)
                    VALUES ($1, $2)
                """, b_id, date.fromisoformat(tomorrow))
        except Exception as e:
            logger.warning(f"[InvestBrand] Error casting vote to DB: {e}")

    _MEMORY_VOTES.setdefault(tomorrow, []).append(b_id)

    return {
        "success": True,
        "brand_id": b_id,
        "message": "Vote logged successfully for tomorrow's challenge!"
    }

@router.post("/puzzles/track-click")
async def track_share_click(payload: TrackClickPayload):
    return {"success": True, "tracked": True}

@router.get("/leaderboard")
async def get_leaderboard(type: str = "daily"):
    """Fetch the leaderboard ranks."""
    pool = await get_db_pool()
    leaderboard_list = []

    if pool:
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT name, avatar_url, total_score, streak
                    FROM public.investbrand_users
                    ORDER BY total_score DESC, streak DESC
                    LIMIT 20
                """)
                for idx, r in enumerate(rows, start=1):
                    leaderboard_list.append({
                        "id": str(idx),
                        "name": r["name"] or f"Player {idx}",
                        "avatar_url": r["avatar_url"] or "",
                        "score": r["total_score"] or 0,
                        "total_score": r["total_score"] or 0,
                        "streak": r["streak"] or 0,
                        "rank": idx
                    })
        except Exception as e:
            logger.warning(f"[InvestBrand] Error querying leaderboard from DB: {e}")

    if not leaderboard_list:
        # Default mock ranking for active community feel
        leaderboard_list = [
            {"id": "1", "name": "Aarav Sharma", "avatar_url": "", "score": 2400, "total_score": 2400, "streak": 14, "rank": 1, "badge": "Silver Virtuoso"},
            {"id": "2", "name": "Priya Patel", "avatar_url": "", "score": 1850, "total_score": 1850, "streak": 9, "rank": 2, "badge": "Bronze Virtuoso"},
            {"id": "3", "name": "Rohan Iyer", "avatar_url": "", "score": 1200, "total_score": 1200, "streak": 5, "rank": 3, "badge": "Copper Virtuoso"},
            {"id": "4", "name": "Ananya Sen", "avatar_url": "", "score": 950, "total_score": 950, "streak": 3, "rank": 4, "badge": "Copper Virtuoso"},
            {"id": "5", "name": "Vikram Malhotra", "avatar_url": "", "score": 600, "total_score": 600, "streak": 2, "rank": 5, "badge": "Junior Virtuoso"}
        ]

    return {"leaderboard": leaderboard_list}

@router.get("/missions")
async def get_missions():
    """Active gamified missions for players."""
    return [
        {
            "id": "m1",
            "title": "First Step",
            "description": "Solve your first daily brand puzzle",
            "xp": 100,
            "badge": "Junior",
            "progress": 100,
            "completed": True
        },
        {
            "id": "m2",
            "title": "Streak Builder",
            "description": "Maintain a 3-day puzzle solving streak",
            "xp": 300,
            "badge": "Copper",
            "progress": 33,
            "completed": False
        },
        {
            "id": "m3",
            "title": "Community Voter",
            "description": "Cast a vote for tomorrow's featured brand",
            "xp": 150,
            "badge": "Voter",
            "progress": 100,
            "completed": True
        },
        {
            "id": "m4",
            "title": "Sector Savant",
            "description": "Correctly identify 5 Energy or IT sector brands",
            "xp": 500,
            "badge": "Bronze",
            "progress": 40,
            "completed": False
        }
    ]

@router.get("/education/locker")
async def get_education_locker():
    """Returns unlocked learning cards and brand insights."""
    cards = []
    for b in NIFTY50_BRANDS[:6]:
        cards.append({
            "id": b.get("id"),
            "brand": b.get("brand"),
            "company": b.get("company"),
            "ticker": b.get("ticker"),
            "sector": b.get("sector"),
            "insight": b.get("insight"),
            "date_unlocked": get_ist_date()
        })
    return {"cards": cards}

@router.get("/education/tip")
async def get_education_tip():
    """Returns the daily Teacher Tip."""
    tips = [
        "Owning one auto stock is risky; an index fund spreads that risk across 50 companies.",
        "Stocks can be volatile short-term but historically compound wealth over 10+ years.",
        "Market cap = share price × total shares; it reveals true enterprise scale.",
        "FMCG stocks (like Hindustan Unilever or ITC) are defensive assets during downturns.",
        "You don't buy 'Pulsar'; you buy Bajaj Auto stock which owns Pulsar and other brands."
    ]
    h = int(hashlib.md5(get_ist_date().encode("utf-8")).hexdigest(), 16)
    tip = tips[h % len(tips)]
    return {
        "tip": tip,
        "author": "InvestBrand Teacher Agent",
        "category": "Portfolio Fundamentals"
    }

@router.get("/users/me")
async def get_user_profile():
    return {
        "id": 1,
        "name": "Market Explorer",
        "email": "explorer@market-rover.app",
        "avatar": "",
        "streak": max(1, len(_MEMORY_SESSIONS)),
        "total_score": max(250, sum(s.get("score", 0) for s in _MEMORY_SESSIONS)),
        "badges": ["Junior Virtuoso", "Brand Sleuth"],
        "created_at": get_ist_date()
    }

@router.get("/users/me/sessions")
async def get_user_sessions():
    return _MEMORY_SESSIONS

@router.get("/auth/config")
async def get_auth_config():
    """Returns runtime authentication configuration (e.g. Google Client ID)."""
    client_id = (os.getenv("IC_GOOGLE_CLIENT_ID") or os.getenv("GOOGLE_CLIENT_ID") or "").strip()
    return {
        "googleClientId": client_id
    }

@router.get("/auth/me")
async def get_auth_me():
    return {
        "user": {
            "id": 1,
            "name": "Market Explorer",
            "email": "explorer@market-rover.app",
            "avatar": "",
            "streak": 1,
            "total_score": 250
        }
    }

@router.post("/auth/social-login")
async def social_login(payload: SocialLoginPayload):
    return {
        "token": "mock_jwt_session_token",
        "user": {
            "id": 1,
            "name": "Market Explorer",
            "email": "explorer@market-rover.app",
            "avatar": "",
            "streak": 1,
            "total_score": 250
        }
    }
