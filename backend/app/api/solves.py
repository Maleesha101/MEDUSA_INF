from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from .. import db, models, schemas, core
from ..core.rate_limit import limit as rate_limit
from ..core.flag_engine import verify_flag, generate_flag
from ..ws.scoreboard import push_scoreboard_update

router = APIRouter(tags=["solves"])


@router.post("/", response_model=schemas.SolveOut, dependencies=[Depends(rate_limit)])
async def submit_solve(
    payload: schemas.SolveIn,
    request: Request,
    db_session: AsyncSession = Depends(db.get_db),
):
    team_id = request.state.team_id
    if not team_id:
        raise HTTPException(status_code=401, detail="Unauthenticated")

    # 1️⃣  fetch challenge row
    chal_row = await db_session.scalar(
        models.challenges.select().where(models.challenges.c.slug == payload.slug)
    )
    if not chal_row:
        raise HTTPException(status_code=404, detail="Challenge not found")

    # 2️⃣  verify flag
    is_valid = await verify_flag(team_id, payload.slug, payload.flag)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Incorrect flag")

    # 3️⃣  check for duplicate solve
    dup = await db_session.scalar(
        models.solves.select().where(
            (models.solves.c.team_id == team_id)
            & (models.solves.c.challenge_id == chal_row.id)
        )
    )
    if dup:
        raise HTTPException(status_code=400, detail="Already solved")

    # 4️⃣  compute dynamic scoring (simple linear decay)
    #   base points - 1 point per previous solve of this challenge
    prev_solves = await db_session.scalar(
        models.solves.select()
        .with_only_columns([sa.func.count()])
        .where(models.solves.c.challenge_id == chal_row.id)
    )
    points_awarded = max(chal_row.points_base - int(prev_solves or 0), 1)

    # 5️⃣  insert solve row
    await db_session.execute(
        models.solves.insert().values(
            team_id=team_id,
            challenge_id=chal_row.id,
            flag_submitted=payload.flag,
            score_awarded=points_awarded,
        )
    )

    # 6️⃣  log audit
    await core.security.log_action(
        team_id=team_id,
        user_id=request.state.user_id,
        action="solve",
        ip_address=request.client.host,
        payload={"challenge_slug": payload.slug, "points": points_awarded},
    )

    # 7️⃣  rebuild leaderboard (simple aggregation)
    result = await db_session.execute(
        """
        SELECT t.id AS team_id, t.display_name, SUM(s.score_awarded) AS total
        FROM teams t
        LEFT JOIN solves s ON t.id = s.team_id
        GROUP BY t.id
        ORDER BY total DESC NULLS LAST, t.display_name
        """
    )
    leaderboard = [
        {"team_id": str(row.team_id), "display_name": row.display_name, "score": int(row.total or 0)}
        for row in result.fetchall()
    ]

    # 8️⃣  push realtime update
    await push_scoreboard_update(leaderboard)

    return schemas.SolveOut(
        message="Correct flag! 🎉",
        points_awarded=points_awarded,
        total_score=leaderboard[0]["score"],  # caller can re‑query if needed
    )
