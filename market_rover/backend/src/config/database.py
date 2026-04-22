"""
Database configuration for Market-Rover backend.
Supports both local PostgreSQL (dev) and Cloud SQL (prod via asyncpg DSN).
Pattern mirrors pledge_rover/backend/src/config/database.py.
"""
import os
import asyncpg
from src.utils.logger import get_logger

logger = get_logger(__name__)

_pool = None


async def get_pool() -> asyncpg.Pool:
    """Returns the global asyncpg connection pool, creating it if needed."""
    global _pool
    if _pool is None:
        _pool = await _create_pool()
    return _pool


async def _create_pool() -> asyncpg.Pool:
    """
    Creates an asyncpg pool.

    - Local dev: reads DATABASE_URL from environment.
    - Cloud Run: uses CLOUD_SQL_CONNECTION_NAME + individual DB_* vars to
      build a socket-based DSN (same pattern as Pledge Rover).
    """
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        # Build Cloud SQL DSN from individual vars (production path)
        conn_name = os.getenv("CLOUD_SQL_CONNECTION_NAME", "")
        db_user   = os.getenv("DB_USER", "postgres")
        db_pass   = os.getenv("DB_PASSWORD", "")
        db_name   = os.getenv("DB_NAME", "postgres")
        socket    = f"/cloudsql/{conn_name}"
        # URL encode credentials and path to prevent "Invalid URL" or DSN parsing errors
        from urllib.parse import quote
        logger.info(f"Connecting to Cloud SQL (asyncpg) | Instance: {conn_name} | Socket: {socket} | DB: {db_name}")
        database_url = f"postgresql://{quote(db_user)}:{quote(db_pass)}@/{quote(db_name)}?host={quote(socket)}"

    logger.info("Initialising asyncpg pool...")
    pool = await asyncpg.create_pool(dsn=database_url, min_size=2, max_size=10)
    logger.info("Database pool ready.")
    return pool


async def close_pool():
    """Gracefully closes the pool on shutdown."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("Database pool closed.")
