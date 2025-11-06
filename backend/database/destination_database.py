from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from utils.config import settings

DESTINATION_DATABASE_URL = (
    f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASS}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DEST_DB_NAME}"
)

destination_engine = create_async_engine(
    DESTINATION_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

DestinationAsyncSessionLocal = sessionmaker(
    bind=destination_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

DestinationBase = declarative_base()

async def get_destination_db():
    async with DestinationAsyncSessionLocal() as session:
        yield session
