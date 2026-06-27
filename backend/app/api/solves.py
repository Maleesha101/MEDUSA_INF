from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from .. import db, models, schemas, core

router = APIRouter(tags=["solves"])

@router.post("/", response_model=schemas.SolveOut)
async def submit_solve(
    payload: schemas.SolveIn,
    db: AsyncSession = Depends(db.get_db),
    request: Request = Depends(),
):
    team_id = request.state.team_id
    challenge = await db.scalar(
        models.challenges.select().where(models.challenges.c.slug == payload.challenge_slug)
    )
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    # -------------------------------------------------
    # Flag verification
    # -------------------------------------------------
    # The secret flag for this team+challenge is stored in Redis (fast) or derived on‑the‑fly.
    expected_flag = await core.flag_engine.get_flag(team_id, challenge.id, db)

    is_correct = core.security.constant_time_compare(payload.flag, expected_flag)

    # -------------------------------------------------
    # Record solve (idempotent – one solve per team/challenge)
    # -------------------------------------------------
    async with db.begin():
        existing = await db.scalar(
            models.solves.select().where(
                (models.solves.c.team_id == team_id) &
                (models.solves.c.challenge_id == challenge.id)
            )
        )
        if existing:
            raise HTTPException(status_code=400, detail="Already solved")

        points = core.scoring.calculate_points(challenge.points_base, challenge.id, db, team_id)

        await db.execute(
            models.solves.insert().values(
                team_id=team_id,
                challenge_id=challenge.id,
                flag_submitted=payload.flag,
                is_correct=is_correct,
                points_awarded=points if is_correct else 0,
                solved_at=core.utils.utcnow(),
            )
        )
    await db.commit()

    # -------------------------------------------------
    # Publish WS event for live scoreboard
    # -------------------------------------------------
    await core.ws.publish_score_update(team_id, points if is_correct else 0)

    return schemas.SolveOut(
        correct=is_correct,
        points_awarded=points if is_correct else 0,
        message="Correct! 🎉" if is_correct else "Incorrect flag",
    )

