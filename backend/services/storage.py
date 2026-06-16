import os
import shutil
from fastapi import UploadFile, HTTPException
from core.config import settings

class StorageService:
    def __init__(self):
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
        os.makedirs(settings.TEMP_DIR, exist_ok=True)

    def save_upload_file(self, file: UploadFile, video_id: str) -> str:
        extension = file.filename.split('.')[-1].lower()
        allowed_extensions = settings.SUPPORTED_VIDEO_FORMATS.split(',') + settings.SUPPORTED_AUDIO_FORMATS.split(',')
        if extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"Unsupported format. Allowed: {allowed_extensions}")

        file_path = os.path.join(settings.UPLOAD_DIR, f"{video_id}.{extension}")
        
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
        finally:
            file.file.close()

        return file_path

storage_service = StorageService()
