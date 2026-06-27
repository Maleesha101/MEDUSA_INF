from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta, datetime
from .. import db, core, models, schemas

router = APIRouter(tags=["auth"])

@router.post("/register")
async def register(payload: schemas.RegisterIn, db: AsyncSession = Depends(db.get_db)):
    # 1️⃣  Verify email not taken
    existing = await db.scalar(
        models.users.select().where(models.users.c.email == payload.email)
    )
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2️⃣  Hash password
    pwd_hash = core.security.hash_password(payload.password)

    # 3️⃣  Insert user + create personal team
    async with db.begin():
        user_id = await db.scalar(
            models.users.insert().values(
                email=payload.email,
                password_hash=pwd_hash,
                full_name=payload.full_name,
                is_active=True,
                is_admin=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ).returning(models.users.c.id)
        )
        # auto‑create a team with the same name as the user
        team_id = await db.scalar(
            models.teams.insert().values(
                name=f"{payload.full_name[:20]}-{user_id.hex[:8]}",
                display_name=payload.full_name,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ).returning(models.teams.c.id)
        )
        await db.execute(
            models.team_members.insert().values(team_id=team_id, user_id=user_id, role="owner")
        )
    await db.commit()
    return {"msg": "registered – you may now log in"}

@router.post("/login")
async def login(payload: schemas.LoginIn, db: AsyncSession = Depends(db.get_db)):
    user = await db.scalar(
        models.users.select().where(models.users.c.email == payload.email)
    )
    if not user or not core.security.verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    # fetch team_id (first team where user is a member)
    team_row = await db.scalar(
        models.team_members.select().where(models.team_members.c.user_id == user.id)
    )
    team_id = team_row.team_id if team_row else None

    access_token = core.security.create_access_token(
        subject=str(user.id),
        team_id=str(team_id),
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = core.security.create_refresh_token(
        subject=str(user.id),
        team_id=str(team_id),
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@router.post("/refresh")
async def refresh(token: schemas.RefreshIn, db: AsyncSession = Depends(db.get_db)):
    payload = core.security.decode_jwt(token.refresh_token, verify_type="refresh")
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    # Ensure token not blacklisted (e.g., on logout)
    if await core.security.is_token_revoked(payload["jti"], db):
        raise HTTPException(status_code=401, detail="Token revoked")
    new_access = core.security.create_access_token(
        subject=payload["sub"],
        team_id=payload["team_id"],
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": new_access, "token_type": "bearer"}

