import os
from pathlib import Path

from fastapi import UploadFile, HTTPException
from core.config import settings


class StorageService:
    def __init__(self):
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        os.makedirs(settings.TEMP_DIR, exist_ok=True)

    def save_upload_file(self, file: UploadFile, video_id: str) -> str:
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Filename is required.")

        filename = Path(file.filename).name
        extension = Path(filename).suffix.lstrip('.').lower()

        if not extension:
            raise HTTPException(
                status_code=400,
                detail="File has no extension.")

        allowed_extensions = settings.SUPPORTED_VIDEO_FORMATS.split(
            ',') + settings.SUPPORTED_AUDIO_FORMATS.split(',')
        if extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format. Allowed: {allowed_extensions}")

        file_path = os.path.join(
            settings.UPLOAD_DIR,
            f"{video_id}.{extension}")

        MAX_CHUNK = 1024 * 1024  # 1MB chunks
        MAX_BYTES = settings.MAX_VIDEO_SIZE_MB * 1024 * 1024
        total_written = 0

        try:
            with open(file_path, "wb") as buffer:
                while chunk := file.file.read(MAX_CHUNK):
                    total_written += len(chunk)
                    if total_written > MAX_BYTES:
                        raise HTTPException(
                            status_code=413,
                            detail=f"File exceeds {settings.MAX_VIDEO_SIZE_MB}MB limit."
                        )
                    buffer.write(chunk)
        except HTTPException:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save file: {str(e)}")
        finally:
            file.file.close()

        return file_path


storage_service = StorageService()
