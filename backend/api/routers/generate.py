import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import os
import json

from core.dependencies import get_owned_video
from models.video import Video
from services.content.artifact_generator import ArtifactGenerator
from services.content.context import LectureContext
from schemas.content import LectureInput, LectureState
from services.llm.llm_manager import LLMManager
from services.merge.builder import load_merged_lecture
from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/generate", tags=["Artifacts"])

class GenerateRequest(BaseModel):
    artifacts: List[str]

@router.post("/{video_id}")
async def generate_artifacts(
    request: GenerateRequest,
    video: Video = Depends(get_owned_video),
):
    """
    Generate specific artifacts on-demand using the pre-computed LearningContext.
    """
    logger.info(f"Received request to generate artifacts {request.artifacts} for video {video.id}")
    
    output_dir = os.path.join(settings.OUTPUT_DIR, str(video.id))
    learning_context_path = os.path.join(output_dir, "learning_context.json")
    
    if not os.path.exists(learning_context_path):
        raise HTTPException(status_code=404, detail="Learning context not found. The pipeline must complete first.")
        
    try:
        with open(learning_context_path, "r", encoding="utf-8") as f:
            state_dict = json.load(f)
            
        # Reconstruct LectureState and LectureContext
        # Note: In a production app, we would use Pydantic models with model_validate 
        # to properly deserialize the complex nested lists.
        # For this prototype, we'll let the generators handle the dicts if possible,
        # or we could parse them properly.
        state = LectureState(**state_dict)
        
        # Load merged_lecture to get the input
        merged_lecture_path = os.path.join(output_dir, "merged_lecture.json")
        merged_lecture = load_merged_lecture(merged_lecture_path)
        
        lecture_input = LectureInput(
            transcript=merged_lecture.full_transcript_text,
            metadata=merged_lecture.metadata,
            segments=merged_lecture.all_transcript_segments,
            frames=[
                {
                    "path": f.frame_path, 
                    "time_sec": f.timestamp_sec, 
                    "ocr": f.ocr_text, 
                    "scene_number": f.scene_number
                } 
                for f in merged_lecture.all_frames
            ]
        )
        context = LectureContext(input=lecture_input, state=state)
        
    except Exception as e:
        logger.error(f"Failed to load learning context: {e}")
        raise HTTPException(status_code=500, detail="Failed to load lecture context.")

    # 3. Generate requested artifacts
    llm_manager = LLMManager()
    artifact_generator = ArtifactGenerator(llm_manager)
    
    results = await artifact_generator.generate(context, request.artifacts)
    
    return {"status": "success", "results": results}
