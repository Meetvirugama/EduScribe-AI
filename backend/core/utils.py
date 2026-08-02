import uuid
from fastapi import HTTPException, status

def parse_video_id(video_id: str) -> uuid.UUID:
    """Parse a video ID string to UUID, raising 422 on invalid format."""
    try:
        return uuid.UUID(video_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid ID format: '{video_id}' is not a valid UUID.",
        )
