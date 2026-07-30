from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from core.config import settings
from core.database import get_db
from core.security import create_access_token, get_current_user
from models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

@router.get("/google/login")
async def google_login():
    # Build the Google login URL
    redirect_uri = "http://localhost:5001/auth/google/callback"
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        f"&response_type=code"
        f"&scope=openid%20email%20profile"
        f"&redirect_uri={redirect_uri}"
        f"&access_type=offline"
    )
    return RedirectResponse(auth_url)

@router.get("/google/callback")
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
    redirect_uri = "http://localhost:5001/auth/google/callback"
    token_url = "https://oauth2.googleapis.com/token"
    
    async with httpx.AsyncClient() as client:
        # Get tokens from Google
        token_res = await client.post(
            token_url,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        token_data = token_res.json()
        if "error" in token_data:
            raise HTTPException(status_code=400, detail=token_data.get("error_description", "Failed to authenticate"))
            
        access_token = token_data["access_token"]
        
        # Get user info
        userinfo_res = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        userinfo = userinfo_res.json()
        
    google_id = userinfo.get("sub")
    email = userinfo.get("email")
    name = userinfo.get("name")
    picture = userinfo.get("picture")
    
    if not google_id:
        raise HTTPException(status_code=400, detail="Google authentication failed")
        
    # Find or create user
    result = await db.execute(select(User).filter(User.google_id == google_id))
    user = result.scalars().first()
    
    if not user:
        user = User(google_id=google_id, email=email, name=name, picture=picture)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
    # Issue local JWT
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    
    # Redirect to frontend dashboard with token
    frontend_url = "http://localhost:5173/auth/callback"
    return RedirectResponse(f"{frontend_url}?token={access_token}")

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "picture": current_user.picture,
        "join_date": current_user.created_at
    }
