"""
api/routers/auth.py — Google OAuth2 Authentication

Security fixes applied:
  ISSUE-03: JWT is no longer passed in the URL fragment (#token=...).
            Instead we issue a short-lived opaque code and the frontend
            POSTs it to /auth/exchange to receive the JWT over HTTPS body.
  SEC-05:   A cryptographically random `state` parameter is generated before
            the OAuth redirect and verified in the callback to prevent CSRF.
"""
import secrets
import time
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from fastapi.responses import RedirectResponse
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.config import settings
from core.database import get_db
from core.security import create_access_token, get_current_user
from models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

# ---------------------------------------------------------------------------
# Redis-backed short-lived token stores (ISSUE-005)
# ---------------------------------------------------------------------------

_STATE_TTL_SECONDS: int = 300   # 5 minutes
_CODE_TTL_SECONDS:  int = 60    # 1 minute

def _get_redis():
    """Lazily connect to Redis. Returns None if REDIS_URL is not set."""
    redis_url = getattr(settings, "REDIS_URL", None)
    if not redis_url:
        return None
    try:
        import redis  # type: ignore
        return redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=1)
    except Exception as exc:
        logger.warning("auth: Redis unavailable (%s) — using in-memory fallback.", exc)
        return None

# Fallback in-memory stores
_pending_states: dict[str, float] = {}
_pending_codes: dict[str, tuple[str, float]] = {}

def _set_state(state: str) -> None:
    r = _get_redis()
    if r:
        r.setex(f"oauth_state:{state}", _STATE_TTL_SECONDS, "1")
    else:
        _pending_states[state] = time.time() + _STATE_TTL_SECONDS

def _verify_state(state: str) -> bool:
    r = _get_redis()
    if r:
        return r.delete(f"oauth_state:{state}") == 1
    else:
        now = time.time()
        if state in _pending_states and now <= _pending_states[state]:
            del _pending_states[state]
            return True
        if state in _pending_states:
            del _pending_states[state]
        return False

def _set_code(code: str, jwt_token: str) -> None:
    r = _get_redis()
    if r:
        r.setex(f"oauth_code:{code}", _CODE_TTL_SECONDS, jwt_token)
    else:
        _pending_codes[code] = (jwt_token, time.time() + _CODE_TTL_SECONDS)

def _pop_code(code: str) -> Optional[str]:
    r = _get_redis()
    if r:
        jwt_token = r.get(f"oauth_code:{code}")
        if jwt_token:
            r.delete(f"oauth_code:{code}")
        return jwt_token
    else:
        now = time.time()
        if code in _pending_codes:
            jwt_token, exp = _pending_codes[code]
            del _pending_codes[code]
            if now <= exp:
                return jwt_token
        return None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/google/login")
async def google_login():
    """
    Redirect the browser to Google's consent page.

    SEC-05: Generates a random `state` value, stores it server-side, and
    includes it in the redirect. The callback verifies it before proceeding.
    """
    state = secrets.token_urlsafe(32)
    _set_state(state)

    redirect_uri = f"{settings.BASE_URL}/auth/google/callback"
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        f"&response_type=code"
        f"&scope=openid%20email%20profile"
        f"&redirect_uri={redirect_uri}"
        f"&access_type=offline"
        f"&state={state}"
    )
    return RedirectResponse(auth_url)


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Google's OAuth2 callback.

    SEC-05: Verifies the `state` parameter against the server-side store to
            prevent CSRF attacks on the OAuth flow.
    ISSUE-03: Issues a short-lived opaque code instead of putting the JWT in
              the URL fragment. The frontend exchanges the code for a JWT via
              POST /auth/exchange.
    """
    # ── CSRF check (SEC-05) ──────────────────────────────────────────────────
    if not state or not _verify_state(state):
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OAuth state. Please try logging in again.",
        )

    # ── Exchange code for Google tokens ──────────────────────────────────────
    redirect_uri = f"{settings.BASE_URL}/auth/google/callback"
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if not token_res.is_success:
            raise HTTPException(
                status_code=502,
                detail="Authentication provider error. Please try again.",
            )

        token_data = token_res.json()
        if "error" in token_data:
            logger.warning(
                "google_callback: OAuth token error — %s: %s",
                token_data.get("error"),
                token_data.get("error_description", "no description"),
            )
            raise HTTPException(
                status_code=400,
                detail="Authentication failed. Please try signing in again.",
            )

        google_access_token = token_data["access_token"]

        # ── Fetch Google user info ────────────────────────────────────────────
        userinfo_res = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {google_access_token}"},
        )
        userinfo = userinfo_res.json()

    google_id = userinfo.get("sub")
    if not google_id:
        raise HTTPException(status_code=400, detail="Google authentication failed")

    email   = userinfo.get("email")
    name    = userinfo.get("name")
    picture = userinfo.get("picture")

    # ── Find or create local user ─────────────────────────────────────────────
    result = await db.execute(select(User).filter(User.google_id == google_id))
    user = result.scalars().first()
    if not user:
        user = User(google_id=google_id, email=email, name=name, picture=picture)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # ── Issue local JWT ───────────────────────────────────────────────────────
    jwt_token = create_access_token(data={"sub": str(user.id), "email": user.email})

    # ── ISSUE-03: Store JWT behind a one-time opaque code ────────────────────
    # The JWT never appears in the URL. The frontend POSTs the code to
    # /auth/exchange and receives the JWT in the response body.
    exchange_code = secrets.token_urlsafe(32)
    _set_code(exchange_code, jwt_token)

    frontend_callback = f"{settings.FRONTEND_URL}/auth/callback"
    return RedirectResponse(f"{frontend_callback}?code={exchange_code}")




class ExchangeRequest(BaseModel):
    code: str

@router.post("/exchange")
async def exchange_code(request: ExchangeRequest):
    """
    Exchange the short-lived one-time code (from the OAuth callback) for a JWT.

    ISSUE-03: This is the secure replacement for #token= in the URL.
    The frontend calls this endpoint immediately on the /auth/callback page.
    The code is single-use and expires in 60 seconds.

    Returns:
        {"access_token": "<jwt>", "token_type": "bearer"}
    """
    jwt_token = _pop_code(request.code)
    if not jwt_token:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired authentication code. Please log in again.",
        )

    return {"access_token": jwt_token, "token_type": "bearer"}



@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "picture": current_user.picture,
        "join_date": current_user.created_at,
    }
