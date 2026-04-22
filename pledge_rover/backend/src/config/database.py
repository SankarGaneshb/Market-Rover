import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from google.cloud.sql.connector import Connector, IPTypes
import pg8000

Base = declarative_base()

# Determine environment (Standard Cloud Run or Cloud SQL presence)
conn_name = os.getenv("CLOUD_SQL_CONNECTION_NAME")
is_production = os.getenv("K_SERVICE") is not None or conn_name is not None

if is_production:
    print(f"Initializing connection to Cloud SQL (ASYNC) via DSN: {conn_name}")
    db_user = os.environ.get("PR_DB_USER", os.environ.get("DB_USER", "postgres"))
    db_pass = os.environ.get("PR_DB_PASSWORD", os.environ.get("DB_PASSWORD", ""))
    db_name = os.environ.get("PR_DB_NAME", os.environ.get("DB_NAME", "pledgerover"))
    socket = f"/cloudsql/{conn_name}"

    # Manual DSN for asyncpg via unix socket
    # Pattern: postgresql://user:pass@/dbname?host=/cloudsql/conn_name
    from urllib.parse import quote
    prod_url = f"postgresql+asyncpg://{quote(db_user)}:{quote(db_pass)}@/{quote(db_name)}?host={quote(socket)}"

    engine = create_async_engine(
        prod_url,
        echo=False,
    )
else:
    # Use local postgres or sqlite for dev
    db_user = os.environ.get("DB_USER")
    db_pass = os.environ.get("DB_PASSWORD")
    db_host = os.environ.get("DB_HOST")
    db_name = os.environ.get("DB_NAME", "pledgerover")

    if db_user and db_pass and db_host:
        db_port = os.environ.get("DB_PORT", "5432")
        local_url = f"postgresql+asyncpg://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        print(f"Initializing connection to local Postgres: {db_name}")
    else:
        # Professional SQLite fallback for laptops
        local_url = f"sqlite+aiosqlite:///./{db_name}.db"
        print(f"Initializing connection to local SQLite: {db_name}.db")

    engine = create_async_engine(local_url, echo=False)

# Create session factory
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def init_db():
    async with engine.begin() as conn:
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
        print("Database schemas initialized.")

async def close_db():
    await engine.dispose()
    print("Database connection closed.")
