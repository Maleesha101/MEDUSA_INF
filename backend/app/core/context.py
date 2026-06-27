from __future__ import annotations

from fastapi import Request

# A thin wrapper that extracts the already‑populated request.state fields.
# Centralising this makes the `container_manager` and `flag_engine` independent
# from FastAPI internals and eases unit‑testing.

def get_current_user_id(request: Request) -> str | None:
    return getattr(request.state, "user_id", None)


def get_current_team_id(request: Request) -> str | None:
    return getattr(request.state, "team_id", None)

