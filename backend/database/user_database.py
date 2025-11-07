from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from utils.config import settings

USER_DATABASE_URL = (
    f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASS}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.USER_DB_NAME}"
)

user_engine = create_async_engine(
    USER_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

UserAsyncSessionLocal = sessionmaker(
    bind=user_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

UserBase = declarative_base()

async def get_db():
    async with UserAsyncSessionLocal() as session:
        yield session