import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from . import config, db, api, ws, core

app = FastAPI(
    title=config.settings.PROJECT_NAME,
    debug=config.settings.DEBUG,
    openapi_url=f"{config.settings.API_V1_STR}/openapi.json",
)

# CORS (frontend served from same domain, but allow localhost dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production to your domain(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session middleware (used only for non‑API cookie flow, optional)
app.add_middleware(SessionMiddleware, secret_key=config.settings.JWT_SECRET_KEY)

# Register routers
app.include_router(api.auth.router, prefix=f"{config.settings.API_V1_STR}/auth")
app.include_router(api.teams.router, prefix=f"{config.settings.API_V1_STR}/teams")
app.include_router(api.challenges.router, prefix=f"{config.settings.API_V1_STR}/challenges")
app.include_router(api.solves.router, prefix=f"{config.settings.API_V1_STR}/solves")
app.include_router(api.admin.router, prefix=f"{config.settings.API_V1_STR}/admin")

# WebSocket endpoint for live scoreboard
app.include_router(ws.router)


# -------------------------------------------------
# Middleware – JWT auth & RLS context setter
# -------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{config.settings.API_V1_STR}/auth/login")

async def set_team_context(request: Request, token: str = Depends(oauth2_scheme)):
    payload = core.security.decode_jwt(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    # Store user and team IDs in request.state for downstream use
    request.state.user_id = payload["sub"]
    request.state.team_id = payload["team_id"]
    # Set PostgreSQL GUC for row‑level security
    await db.session.set_current_team(payload["team_id"])

app.middleware("http")(set_team_context)


# -------------------------------------------------
# Exception handlers (e.g., rate limit)
# -------------------------------------------------
@app.exception_handler(core.rate_limit.RateLimitException)
async def rate_limit_handler(request: Request, exc: core.rate_limit.RateLimitException):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": f"Rate limit exceeded. Retry after {exc.retry_after}s"},
    )

# -------------------------------------------------
# Root health check
# -------------------------------------------------
@app.get("/", tags=["health"])
async def root():
    return {"message": "MEDUSA CTF Platform – API is alive"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=config.settings.DEBUG)

