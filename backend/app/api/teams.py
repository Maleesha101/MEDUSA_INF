from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from .. import db, models, schemas, core
from ..core.security import log_action

router = APIRouter(tags=["teams"])


@router.get("/me", response_model=schemas.TeamOut)
async def read_my_team(request: Request, db_session: AsyncSession = Depends(db.get_db)):
    team_id = request.state.team_id
    if not team_id:
        raise HTTPException(status_code=401, detail="Unauthenticated")
    team = await db_session.scalar(models.teams.select().where(models.teams.c.id == team_id))
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return schemas.TeamOut.from_orm(team)


@router.post("/", response_model=schemas.TeamOut)
async def create_team(
    payload: schemas.TeamOut,
    request: Request,
    db_session: AsyncSession = Depends(db.get_db),
):
    # Only an authenticated user can create a second team (optional policy)
    if not request.state.user_id:
        raise HTTPException(status_code=401, detail="Unauthenticated")

    # Ensure unique name
    exists = await db_session.scalar(models.teams.select().where(models.teams.c.name == payload.name))
    if exists:
        raise HTTPException(status_code=400, detail="Team name already taken")

    stmt = models.teams.insert().values(
        name=payload.name,
        display_name=payload.display_name,
        created_at=db_mod._now(),
        updated_at=db_mod._now(),
    ).returning(models.teams.c.id)
    team_id = await db_session.scalar(stmt)

    # Add creator as owner
    await db_session.execute(
        models.team_members.insert().values(team_id=team_id, user_id=request.state.user_id, role="owner")
    )
    await log_action(
        team_id=str(team_id),
        user_id=request.state.user_id,
        action="team_create",
        ip_address=request.client.host,
        payload={"team_name": payload.name},
    )
    return schemas.TeamOut(id=str(team_id), name=payload.name, display_name=payload.display_name)

