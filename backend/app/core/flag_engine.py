from __future__ import annotations

import hashlib
import secrets
from typing import Any

from ..db import models
from ..db import db as db_mod
from ..config import settings


def _render_template(template: str, *, team_id: str, challenge_id: str) -> str:
    """
    Very small templating engine used for flag generation.
    Supported placeholders:
        {team_id}  – UUID of the team (raw)
        {challenge_id} – UUID of the challenge (raw)
        {hash} – SHA‑256 of (team_id + challenge_id + secret)
    """
    secret = settings.JWT_SECRET_KEY  # a secret value already loaded from env
    hash_part = hashlib.sha256(f"{team_id}{challenge_id}{secret}".encode()).hexdigest()[:8]
    return template.format(team_id=team_id, challenge_id=challenge_id, hash=hash_part)


async def generate_flag(team_id: str, challenge_row: Any) -> str:
    """
    Return the hidden flag for a given team‑challenge pair.
    The flag is *not* stored in the DB – it is recomputed on demand.
    """
    return _render_template(
        challenge_row.flags_template,
        team_id=team_id,
        challenge_id=str(challenge_row.id),
    )


async def verify_flag(team_id: str, challenge_slug: str, submitted: str) -> bool:
    """Check whether a submitted flag matches the generated one."""
    async with db_mod.engine.begin() as conn:
        result = await conn.execute(
            models.challenges.select().where(models.challenges.c.slug == challenge_slug)
        )
        chal = result.fetchone()
        if not chal:
            return False
        expected = await generate_flag(team_id, chal)
        # Constant‑time comparison to mitigate timing attacks
        return secrets.compare_digest(expected, submitted.strip())
