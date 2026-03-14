from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ChapterOut(BaseModel):
    id: int
    file_id: int
    chapter_index: int
    title: str
    start_page: int
    end_page: int
    audio_bucket_name: Optional[str] = None
    audio_object_name: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChapterAudioResponse(BaseModel):
    chapter_id: int = Field(..., description="Chapter identifier")
    url: str = Field(..., description="Presigned URL for streaming audio")
    expires_in_seconds: int = Field(..., description="URL validity in seconds")

    model_config = {
        "json_schema_extra": {
            "example": {
                "chapter_id": 3,
                "url": "http://minio:9000/completed-files/1/3.wav?...",
                "expires_in_seconds": 3600,
            }
        }
    }
