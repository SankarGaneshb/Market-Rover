import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def setup_db():
    dsn = "postgresql://postgres:postgres@localhost:5432/postgres"
    conn = await asyncpg.connect(dsn=dsn)

    # Create database if not exists
    try:
        await conn.execute("CREATE DATABASE investcraft")
        print("Created database: investcraft")
    except asyncpg.exceptions.DuplicateDatabaseError:
        print("Database already exists.")
    await conn.close()

    # Connect to new db and create tables
    dsn = os.getenv("DATABASE_URL")
    conn = await asyncpg.connect(dsn=dsn)

    tables = [
        """
        CREATE TABLE IF NOT EXISTS public.user_activity_log (
            id SERIAL PRIMARY KEY,
            user_id TEXT NOT NULL,
            action_type TEXT NOT NULL,
            platform TEXT DEFAULT 'WEB',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS public.agent_memory_ltm (
            user_id TEXT NOT NULL,
            ticker TEXT NOT NULL,
            stance TEXT NOT NULL,
            logic_summary TEXT,
            analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, ticker)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS public.social_shares (
            id SERIAL PRIMARY KEY,
            user_id TEXT NOT NULL,
            platform TEXT NOT NULL,
            content_type TEXT NOT NULL,
            recipient_count INTEGER DEFAULT 1,
            share_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    ]

    for table_sql in tables:
        await conn.execute(table_sql)

    print("All tables initialized successfully.")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(setup_db())
