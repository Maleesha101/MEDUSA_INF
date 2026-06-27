from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from ..config import settings

engine = create_async_engine(settings.POSTGRES_DSN, echo=False, future=True)

AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)

# Dependency for FastAPI endpoints
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# Helper to set the RLS GUC for the current request
async def set_current_team(team_id: str):
    async with engine.begin() as conn:
        await conn.execute(
            "SELECT public.set_current_team(:tid)", {"tid": team_id}
        )
