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

# Determine environment
is_production = os.getenv("NODE_ENV") == "production"

if is_production:
    print(f"Initializing connection to Cloud SQL: {os.getenv('CLOUD_SQL_CONNECTION_NAME')}")
    # The SQLAlchemy engine will indirectly call getconn()
    engine = create_async_engine(
        "postgresql+pg8000://",
        creator=getconn,
        echo=False,
    )
else:
    # Use local postgres or sqlite for dev if desired, assuming standard postgres here
    db_user = os.environ.get("DB_USER", "postgres")
    db_pass = os.environ.get("DB_PASSWORD", "password")
    db_host = os.environ.get("DB_HOST", "localhost")
    db_port = os.environ.get("DB_PORT", "5432")
    db_name = os.environ.get("DB_NAME", "pledgerover")
    
    local_url = f"postgresql+asyncpg://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    print(f"Initializing connection to local database: {db_name}")
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
