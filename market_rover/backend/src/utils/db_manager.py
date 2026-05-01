import os
import asyncio
import asyncpg
from urllib.parse import quote_plus
from datetime import datetime
from src.utils.logger import get_logger

logger = get_logger(__name__)

class DBManager:
    """
    Handles async connections to the Market-Rover PostgreSQL instance.
    Supports user activity tracking, social loops, and agent memory.
    """

    def __init__(self):
        self.pool = None
        self._lock = asyncio.Lock()

    async def connect(self):
        async with self._lock:
            if not self.pool:
                # Fetch env vars inside connect to pick up dynamic changes/dotenv
                dsn       = os.getenv("DATABASE_URL")
                conn_name = os.getenv("CLOUD_SQL_CONNECTION_NAME")
                user      = os.getenv("DB_USER", "postgres")
                password  = os.getenv("DB_PASSWORD", "")
                db_name   = os.getenv("DB_NAME", "market_rover")
                db_host   = os.getenv("DB_HOST", "localhost")
                db_port   = os.getenv("DB_PORT", "5432")

                try:
                    if dsn:
                        logger.info("Connecting to PostgreSQL using DSN...")
                        self.pool = await asyncpg.create_pool(dsn=dsn)
                    else:
                        # GoA Rule: Always URL-encode database credentials in DSN-like construction
                        encoded_user = quote_plus(user)
                        encoded_password = quote_plus(password)

                        host = f"/cloudsql/{conn_name}" if conn_name else db_host
                        port = int(db_port)

                        logger.info(f"Connecting to PostgreSQL (Host: {host})...")

                        self.pool = await asyncpg.create_pool(
                            user=user,
                            password=password,
                            database=db_name,
                            host=host,
                            port=port,
                            min_size=5,
                            max_size=20
                        )
                    logger.info(f"Successfully connected to PostgreSQL Pool ({ 'Socket' if conn_name else 'TCP' }).")

                    # Ensure schema is initialized
                    try:
                        schema_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'schema.sql')
                        if os.path.exists(schema_path):
                            with open(schema_path, 'r', encoding='utf-8') as f:
                                schema_sql = f.read()
                            async with self.pool.acquire() as conn:
                                await conn.execute(schema_sql)
                            logger.info("Database schema initialized automatically.")
                    except Exception as e:
                        logger.error(f"Failed to auto-initialize schema: {e}")

                except Exception as e:
                    logger.error(f"PostgreSQL Connection Error: {e}")
                    raise

    async def log_activity(self, user_handle: str, action: str, platform: str = "WEB"):
        """Logs user login/interaction events."""
        query = """
            INSERT INTO public.user_activity_log (user_id, action_type, platform)
            VALUES ($1, $2, $3)
        """
        async with self.pool.acquire() as conn:
            await conn.execute(query, user_handle, action, platform)

    async def store_memory(self, user_handle: str, ticker: str, stance: str, logic: str):
        """Stores final analysis conclusion as Long-Term Memory (LTM)."""
        query = """
            INSERT INTO public.agent_memory_ltm (user_id, ticker, stance, logic_summary)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id, ticker) DO UPDATE
            SET stance = $3, logic_summary = $4, analysis_date = CURRENT_TIMESTAMP
        """
        async with self.pool.acquire() as conn:
            await conn.execute(query, user_handle, ticker, stance, logic)

    async def get_memory(self, user_handle: str, ticker: str):
        """Retrieves the last known stance for the user/ticker pair."""
        query = """
            SELECT stance, logic_summary, analysis_date
            FROM public.agent_memory_ltm
            WHERE user_id = $1 AND ticker = $2
            ORDER BY analysis_date DESC LIMIT 1
        """
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, user_handle, ticker)

    async def record_share(self, user_handle: str, platform: str, content_type: str, reach: int = 1):
        """Tracks social engagement (WhatsApp/X/etc)."""
        query = """
            INSERT INTO public.social_shares (user_id, platform, content_type, recipient_count)
            VALUES ($1, $2, $3, $4)
        """
        async with self.pool.acquire() as conn:
            await conn.execute(query, user_handle, platform, content_type, reach)

    async def set_user_persona(self, user_handle: str, persona: str):
        """Saves the user's investor persona (e.g., Hunter, Defender)."""
        # Ensure table exists first (Lightweight idempotent check)
        setup_query = """
            CREATE TABLE IF NOT EXISTS public.user_profiles (
                user_id TEXT PRIMARY KEY,
                persona TEXT DEFAULT 'Neutral',
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        query = """
            INSERT INTO public.user_profiles (user_id, persona, last_updated)
            VALUES ($1, $2, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id) DO UPDATE SET persona = $2, last_updated = CURRENT_TIMESTAMP
        """
        async with self.pool.acquire() as conn:
            await conn.execute(setup_query)
            await conn.execute(query, user_handle, persona)

    async def get_user_persona(self, user_handle: str):
        """Retrieves the investor persona."""
        query = "SELECT persona FROM public.user_profiles WHERE user_id = $1"
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, user_handle)

    async def get_forecast_history(self, user_handle: str):
        """Retrieves all historical analysis stances as a forecast tracker."""
        query = """
            SELECT ticker, stance, logic_summary, analysis_date
            FROM public.agent_memory_ltm
            WHERE user_id = $1
            ORDER BY analysis_date DESC
        """
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, user_handle)

# Global singleton
db = DBManager()
