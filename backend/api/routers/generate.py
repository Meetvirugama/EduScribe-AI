import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_owned_video
from core.database import get_db
from models.video import Video
from models.artifact import Artifact, ArtifactStatus
from core.config import settings
from worker import enqueue_artifact_job

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/generate", tags=["Artifacts"])

class GenerateRequest(BaseModel):
    artifacts: List[str]

@router.post("/{video_id}")
async def generate_artifacts(
    request: GenerateRequest,
    video: Video = Depends(get_owned_video),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate specific artifacts on-demand using the pre-computed LearningContext.
    """
    logger.info(f"Received request to generate artifacts {request.artifacts} for video {video.id}")
    
    output_dir = os.path.join(settings.OUTPUT_DIR, str(video.id))
    learning_context_path = os.path.join(output_dir, "learning_context.json")
    
    if not os.path.exists(learning_context_path):
        raise HTTPException(status_code=404, detail="Learning context not found. The pipeline must complete first.")
        
    job_ids = []
    
    for artifact_type in request.artifacts:
        # 1. Create or update artifact as PENDING in DB
        result = await db.execute(
            select(Artifact).where(Artifact.video_id == video.id, Artifact.artifact_type == artifact_type)
        )
        artifact = result.scalar_one_or_none()
        
        if artifact:
            artifact.status = ArtifactStatus.PENDING
            artifact.error_message = None
        else:
            artifact = Artifact(
                video_id=video.id,
                artifact_type=artifact_type,
                status=ArtifactStatus.PENDING
            )
            db.add(artifact)
            
        await db.commit()
        
        # 2. Enqueue job
        job_id = await enqueue_artifact_job(str(video.id), artifact_type)
        job_ids.append({
            "artifact_type": artifact_type,
            "job_id": job_id
        })
    
    return {"status": "success", "jobs": job_ids}

@router.get("/{video_id}/artifacts")
async def get_artifacts(
    video: Video = Depends(get_owned_video),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve all artifacts generated for this video.
    """
    result = await db.execute(
        select(Artifact).where(Artifact.video_id == video.id).order_by(Artifact.created_at.desc())
    )
    artifacts = result.scalars().all()
    
    return {
        "status": "success",
        "artifacts": [
            {
                "id": str(a.id),
                "artifact_type": a.artifact_type,
                "status": a.status.value,
                "content": a.content,
                "quality": a.quality,
                "error_message": a.error_message,
                "updated_at": a.updated_at
            } for a in artifacts
        ]
    }
