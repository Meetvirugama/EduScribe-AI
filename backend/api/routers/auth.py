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
from fastapi.responses import RedirectResponse, JSONResponse
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
# In-memory short-lived token stores
# In production these should be backed by Redis with TTL.
# ---------------------------------------------------------------------------

# state → expiry_ts  (CSRF protection for OAuth flow — SEC-05)
_pending_states: dict[str, float] = {}

# code → (jwt, expiry_ts)  (one-time code for token exchange — ISSUE-03)
_pending_codes: dict[str, tuple[str, float]] = {}

_STATE_TTL_SECONDS: float = 300.0   # 5 minutes
_CODE_TTL_SECONDS:  float = 60.0    # 1 minute


def _cleanup_expired() -> None:
    """Remove expired entries to prevent unbounded memory growth."""
    now = time.time()
    for k in [k for k, v in _pending_states.items() if now > v]:
        del _pending_states[k]
    for k in [k for k, (_, exp) in _pending_codes.items() if now > exp]:
        del _pending_codes[k]


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
    _cleanup_expired()
    state = secrets.token_urlsafe(32)
    _pending_states[state] = time.time() + _STATE_TTL_SECONDS

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
    _cleanup_expired()

    # ── CSRF check (SEC-05) ──────────────────────────────────────────────────
    now = time.time()
    if not state or state not in _pending_states or now > _pending_states[state]:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OAuth state. Please try logging in again.",
        )
    del _pending_states[state]  # consume it — one-time use

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
            raise HTTPException(
                status_code=400,
                detail=token_data.get("error_description", "Failed to authenticate"),
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
    _pending_codes[exchange_code] = (jwt_token, time.time() + _CODE_TTL_SECONDS)

    frontend_callback = f"{settings.FRONTEND_URL}/auth/callback"
    return RedirectResponse(f"{frontend_callback}?code={exchange_code}")


@router.post("/exchange")
async def exchange_code(code: str):
    """
    Exchange the short-lived one-time code (from the OAuth callback) for a JWT.

    ISSUE-03: This is the secure replacement for #token= in the URL.
    The frontend calls this endpoint immediately on the /auth/callback page.
    The code is single-use and expires in 60 seconds.

    Returns:
        {"access_token": "<jwt>", "token_type": "bearer"}
    """
    _cleanup_expired()
    now = time.time()

    entry = _pending_codes.get(code)
    if not entry or now > entry[1]:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired authentication code. Please log in again.",
        )

    jwt_token, _ = entry
    del _pending_codes[code]   # consume — single use

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
