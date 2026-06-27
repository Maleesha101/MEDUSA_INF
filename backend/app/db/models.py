from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import MetaData, Table, Column, String, Boolean, Integer, DateTime, ForeignKey, JSON

metadata = MetaData(schema="public")  # default schema

# ── Users ───────────────────────────────────────────────────────
users = Table(
    "users",
    metadata,
    Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
    Column("email", String, unique=True, nullable=False, index=True),
    Column("password_hash", String, nullable=False),
    Column("full_name", String, nullable=False),
    Column("is_active", Boolean, default=True, nullable=False),
    Column("is_admin", Boolean, default=False, nullable=False),
    Column("created_at", DateTime(timezone=True), default=datetime.utcnow, nullable=False),
    Column("updated_at", DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False),
)

# ── Teams ───────────────────────────────────────────────────────
teams = Table(
    "teams",
    metadata,
    Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
    Column("name", String, unique=True, nullable=False),
    Column("display_name", String, nullable=False),
    Column("created_at", DateTime(timezone=True), default=datetime.utcnow, nullable=False),
    Column("updated_at", DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False),
)

# ── Team‑Members (many‑to‑many) ───────────────────────────────────
team_members = Table(
    "team_members",
    metadata,
    Column("team_id", sa.UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", sa.UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role", String, nullable=False, default="member"),  # owner / admin / member
    Column("joined_at", DateTime(timezone=True), default=datetime.utcnow, nullable=False),
)

# ── Challenges (catalog) ───────────────────────────────────────
challenges = Table(
    "challenges",
    metadata,
    Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
    Column("slug", String, unique=True, nullable=False, index=True),
    Column("title", String, nullable=False),
    Column("category", String, nullable=False),
    Column("description", String, nullable=False),
    Column("difficulty", String, nullable=False),  # easy / medium / hard / extreme
    Column("points_base", Integer, nullable=False, default=100),
    Column("flags_template", String, nullable=False),  # e.g. "MEDUSA{team_id}-{challenge_id}"
    Column("created_at", DateTime(timezone=True), default=datetime.utcnow, nullable=False),
)

# ── Solves (per‑team) ───────────────────────────────────────────
solves = Table(
    "solves",
    metadata,
    Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
    Column("team_id", sa.UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False),
    Column("challenge_id", sa.UUID(as_uuid=True), ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False),
    Column("solved_at", DateTime(timezone=True), default=datetime.utcnow, nullable=False),
    Column("score_awarded", Integer, nullable=False),
    Column("flag_submitted", String, nullable=False),
    sa.UniqueConstraint("team_id", "challenge_id", name="uq_team_challenge"),
)

# ── Audit Log (write‑only) ───────────────────────────────────────
audit_logs = Table(
    "audit_logs",
    metadata,
    Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
    Column("team_id", sa.UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL")),
    Column("user_id", sa.UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")),
    Column("action", String, nullable=False),
    Column("ip_address", String, nullable=True),
    Column("payload", JSON, nullable=True),
    Column("created_at", DateTime(timezone=True), default=datetime.utcnow, nullable=False),
)

# Export for import convenience
__all__ = [
    "users",
    "teams",
    "team_members",
    "challenges",
    "solves",
    "audit_logs",
    "metadata",
]
