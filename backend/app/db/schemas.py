from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, validator


# ── Auth ───────────────────────────────────────────────────────
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshIn(BaseModel):
    refresh_token: str


# ── Team ───────────────────────────────────────────────────────
class TeamOut(BaseModel):
    id: str
    name: str
    display_name: str

    class Config:
        orm_mode = True


# ── Challenge Catalog ───────────────────────────────────────────
class ChallengeOut(BaseModel):
    id: str
    slug: str
    title: str
    category: str
    difficulty: str
    points_base: int

    class Config:
        orm_mode = True


class ChallengeDetail(ChallengeOut):
    description: str
    endpoint: Optional[str] = None  # filled at runtime with per‑team container host


# ── Solve Submission ───────────────────────────────────────────
class SolveIn(BaseModel):
    slug: str
    flag: str = Field(..., min_length=1)


class SolveOut(BaseModel):
    message: str
    points_awarded: int
    total_score: int


# ── Admin ───────────────────────────────────────────────────────
class ChallengeCreate(BaseModel):
    slug: str
    title: str
    category: str
    description: str
    difficulty: str
    points_base: int = 100
    flags_template: str = "MEDUSA{team_id}-{challenge_id}"

    @validator("slug")
    def _slug_must_be_alnum(cls, v: str) -> str:
        if not v.isidentifier():
            raise ValueError("slug must be a valid python identifier (letters, numbers, _)")  # noqa: E501
        return v


class ChallengeUpdate(BaseModel):
    title: Optional[str]
    category: Optional[str]
    description: Optional[str]
    difficulty: Optional[str]
    points_base: Optional[int]
    flags_template: Optional[str]


# ── Misc ───────────────────────────────────────────────────────
class APIMessage(BaseModel):
    msg: str
