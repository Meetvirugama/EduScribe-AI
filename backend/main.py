from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import video, auth
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="EduScribe AI Phase 1 API")

app.include_router(video.router)
app.include_router(auth.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("storage", exist_ok=True)
app.mount("/storage", StaticFiles(directory="storage"), name="storage")

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "EduScribe AI Backend is running (FastAPI)"}
