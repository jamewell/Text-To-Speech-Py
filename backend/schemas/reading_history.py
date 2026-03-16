from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReadingHistoryUpdate(BaseModel):
    chapter_id: Optional[int] = None
    position_seconds: float = Field(..., ge=0, description="Playback position in seconds")


class ReadingHistoryOut(BaseModel):
    id: int
    user_id: int
    file_id: int
    chapter_id: Optional[int] = None
    position_seconds: float
    updated_at: datetime

    model_config = {"from_attributes": True}


class HistoryListResponse(BaseModel):
    history: list[ReadingHistoryOut]
    total: int
    page: int
    page_size: int
