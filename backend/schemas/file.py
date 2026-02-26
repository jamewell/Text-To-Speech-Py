from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class FileUploadResponse(BaseModel):

    id:int = Field(..., description="Unique file identifier")
    original_filename: str = Field(..., description="Original name of the uploaded file")
    stored_filename: str = Field(..., description="Internal storage name")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type of the file")
    status: str = Field(..., description="Current processing status")
    upload_date: datetime = Field(..., description="Uploaded timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "original_filename": "document.pdf",
                "stored_filename": "user_123_1698765432_a1b2c3d4.pdf",
                "file_size": 1048576,
                "mime_type": "application/pdf",
                "status": "pending",
                "upload_date": "2025-10-31T12:00:00Z",
            }
        }
    }


class FileOut(BaseModel):
    id: int
    user_id: int
    original_filename: str
    stored_filename: str
    file_size: int
    mime_type: str
    bucket_name: str
    status: str
    error_message: Optional[str] = None
    upload_date: datetime
    processed_date: Optional[datetime] = None

    model_config = {
        "from_attributes": True,
        "json_encoder": {
            datetime: lambda v: v.isoformat()
        }
    }


class FileListResponse(BaseModel):

    files: list[FileOut]
    total: int
    page: int
    page_size: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "files": [],
                "total": 10,
                "page": 1,
                "page_size": 20
            }
        }
    }


class FileStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(pending|processing|completed|failed)$")
    error_message: Optional[str] = None

    @field_validator("error_message")
    @classmethod
    def validate_error_message(cls, v, info):
        if info.data.get("status") == "failed" and not v:
            raise ValueError("error_message is required when status is 'failed'")
        return v


class FileDeleteResponse(BaseModel):
    message: str
    file_id: int
    deleted: bool

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "File deleted successfully",
                "file_id": 22,
                "deleted": True
            }
        }
    }
