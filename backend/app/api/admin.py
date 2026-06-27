from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from .. import db, models, schemas, core
from ..core.security import log_action

router = APIRouter(tags=["admin"])


def _require_admin(request: Request):
    if not request.state.user_id:
        raise HTTPException(status_code=401, detail="Unauthenticated")
    # Simple admin check – you could also query the DB for `is_admin`
    # For this demo we treat the first registered user as admin (env var can override)
    if request.state.user_id != "admin-id-placeholder":  # replace in prod
        raise HTTPException(status_code=403, detail="Admin privileges required")


@router.post("/challenges", response_model=schemas.ChallengeOut)
async def create_challenge(
    payload: schemas.ChallengeCreate,
    request: Request,
    db_session: AsyncSession = Depends(db.get_db),
):
    _require_admin(request)

    # Ensure slug uniqueness
    exists = await db_session.scalar(models.challenges.select().where(models.challenges.c.slug == payload.slug))
    if exists:
        raise HTTPException(status_code=400, detail="Slug already exists")

    stmt = models.challenges.insert().values(
        slug=payload.slug,
        title=payload.title,
        category=payload.category,
        description=payload.description,
        difficulty=payload.difficulty,
        points_base=payload.points_base,
        flags_template=payload.flags_template,
    ).returning(models.challenges.c.id)

    chal_id = await db_session.scalar(stmt)

    await log_action(
        team_id=None,
        user_id=request.state.user_id,
        action="admin_create_challenge",
        ip_address=request.client.host,
        payload={"challenge_id": str(chal_id), "slug": payload.slug},
    )
    return schemas.ChallengeOut(
        id=str(chal_id),
        slug=payload.slug,
        title=payload.title,
        category=payload.category,
        difficulty=payload.difficulty,
        points_base=payload.points_base,
    )


@router.put("/challenges/{slug}", response_model=schemas.ChallengeOut)
async def update_challenge(
    slug: str,
    payload: schemas.ChallengeUpdate,
    request: Request,
    db_session: AsyncSession = Depends(db.get_db),
):
    _require_admin(request)

    stmt = (
        models.challenges.update()
        .where(models.challenges.c.slug == slug)
        .values(**{k: v for k, v in payload.dict().items() if v is not None})
        .returning(*models.challenges.c)
    )
    result = await db_session.execute(stmt)
    updated = result.fetchone()
    if not updated:
        raise HTTPException(status_code=404, detail="Challenge not found")

    await log_action(
        team_id=None,
        user_id=request.state.user_id,
        action="admin_update_challenge",
        ip_address=request.client.host,
        payload={"slug": slug, "fields": payload.dict(exclude_unset=True)},
    )
    return schemas.ChallengeOut.from_orm(updated)


@router.delete("/challenges/{slug}", status_code=204)
async def delete_challenge(
    slug: str,
    request: Request,
    db_session: AsyncSession = Depends(db.get_db),
):
    _require_admin(request)

    stmt = models.challenges.delete().where(models.challenges.c.slug == slug)
    result = await db_session.execute(stmt)
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Challenge not found")

    await log_action(
        team_id=None,
        user_id=request.state.user_id,
        action="admin_delete_challenge",
        ip_address=request.client.host,
        payload={"slug": slug},
    )
    return {}
