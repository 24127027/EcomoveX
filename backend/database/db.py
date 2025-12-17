from contextlib import contextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from utils.config import settings

USER_DATABASE_URL = (
    f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASS}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

# Sync database URL for FAISS initialization
SYNC_DATABASE_URL = (
    f"postgresql://{settings.DB_USER}:{settings.DB_PASS}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

engine = create_async_engine(
    USER_DATABASE_URL, echo=False, pool_pre_ping=True, pool_size=10, max_overflow=20
)

UserAsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

# Lazy initialization for sync engine
_sync_engine = None
_SyncSessionLocal = None


def _get_sync_engine():
    """Lazy initialization of sync engine"""
    global _sync_engine, _SyncSessionLocal
    if _sync_engine is None:
        try:
            _sync_engine = create_engine(SYNC_DATABASE_URL, echo=False, pool_pre_ping=True)
            _SyncSessionLocal = sessionmaker(bind=_sync_engine, class_=Session, expire_on_commit=False)
        except Exception as e:
            print(f"⚠️ Failed to create sync engine (psycopg2 may be missing): {e}")
            print("   Install with: pip install psycopg2-binary")
            raise
    return _sync_engine, _SyncSessionLocal


async def get_db():
    async with UserAsyncSessionLocal() as session:
        yield session


@contextmanager
def get_sync_session():
    """Get synchronous database session for FAISS index building"""
    _, SyncSessionLocal = _get_sync_engine()
    session = SyncSessionLocal()
    try:
        yield session
    finally:
        session.close()
