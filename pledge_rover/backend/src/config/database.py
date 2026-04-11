import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from google.cloud.sql.connector import Connector, IPTypes
import pg8000

Base = declarative_base()

# initialize Cloud SQL Python Connector object
connector = Connector()

def getconn() -> pg8000.dbapi.Connection:
    conn: pg8000.dbapi.Connection = connector.connect(
        os.environ["CLOUD_SQL_CONNECTION_NAME"],
        "pg8000",
        user=os.environ.get("PR_DB_USER", os.environ.get("DB_USER", "postgres")),
        password=os.environ.get("PR_DB_PASSWORD", os.environ.get("DB_PASSWORD", "password")),
        db=os.environ.get("PR_DB_NAME", os.environ.get("DB_NAME", "pledgerover")),
        ip_type=IPTypes.PUBLIC,
    )
    return conn

# Determine environment (Standard Cloud Run or Cloud SQL presence)
is_production = os.getenv("K_SERVICE") is not None or os.getenv("CLOUD_SQL_CONNECTION_NAME") is not None

if is_production:
    print(f"Initializing connection to Cloud SQL (ASYNC): {os.getenv('CLOUD_SQL_CONNECTION_NAME')}")
    
    async def get_async_conn():
        # Use connect_async for non-blocking I/O
        return await connector.connect_async(
            os.environ["CLOUD_SQL_CONNECTION_NAME"],
            "asyncpg",
            user=os.environ.get("PR_DB_USER", os.environ.get("DB_USER", "postgres")),
            password=os.environ.get("PR_DB_PASSWORD", os.environ.get("DB_PASSWORD", "password")),
            db=os.environ.get("PR_DB_NAME", os.environ.get("DB_NAME", "pledgerover")),
            ip_type=IPTypes.PUBLIC,
        )

    # Use async_creator for SQLAlchemy 1.4+
    engine = create_async_engine(
        "postgresql+asyncpg://",
        async_creator=get_async_conn,
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
    if is_production:
        connector.close()
    await engine.dispose()
    print("Database connection closed.")
