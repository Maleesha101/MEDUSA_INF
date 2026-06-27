
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from .. import db, models, schemas, core

router = APIRouter(tags=["challenges"])

@router.get("/", response_model=list[schemas.ChallengeOut])
async def list_challenges(db: AsyncSession = Depends(db.get_db)):
    rows = await db.scalars(models.challenges.select())
    return [schemas.ChallengeOut.from_orm(r) for r in rows]

@router.get("/{slug}", response_model=schemas.ChallengeDetail)
async def get_challenge(slug: str, db: AsyncSession = Depends(db.get_db)):
    chal = await db.scalar(
        models.challenges.select().where(models.challenges.c.slug == slug)
    )
    if not chal:
        raise HTTPException(status_code=404, detail="Challenge not found")
    # Build per‑team endpoint URL (container DNS name)
    team_id = core.context.get_current_team_id()
    container_host = f"team-{team_id}-{slug}"
    endpoint = f"http://{container_host}:8080"
    return schemas.ChallengeDetail.from_orm(chal, extra={"endpoint": endpoint})
