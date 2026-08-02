from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from api.routers import video, auth
from api.routers import frames as frames_router
from api.routers import notes as notes_router
from fastapi.staticfiles import StaticFiles
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("../storage", exist_ok=True)
    yield

app = FastAPI(title="EduScribe AI Phase 1 API", lifespan=lifespan)

app.include_router(video.router)
app.include_router(auth.router)
app.include_router(frames_router.router)
app.include_router(notes_router.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/storage", StaticFiles(directory="../storage"), name="storage")

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "EduScribe AI Backend is running (FastAPI)"}
