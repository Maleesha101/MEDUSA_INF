from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from ..config import settings

# ── Async engine ───────────────────────────────────────────────────────
engine: AsyncEngine = create_async_engine(
    settings.POSTGRES_DSN,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
)

# ── Session factory ───────────────────────────────────────────────────
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a DB session and ensures cleanup."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Helper to set PostgreSQL GUC for row‑level security (RLS) ────────
async def set_current_team(team_id: str | None) -> None:
    """Set a GUC that can be referenced in RLS policies.

    The backend uses `session.set_local(session_user_id => ...)` via raw SQL.
    """
    if not team_id:
        return
    async with engine.begin() as conn:
        await conn.execute(
            f"SET app.current_team_id = '{team_id}';"
        )

