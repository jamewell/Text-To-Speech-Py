import datetime
from enum import Enum

from sqlalchemy import Column, Integer, ForeignKey, String, BigInteger, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import relationship

from core.database import Base


class FileStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class File(Base):
    """
   Model for storing file metadata.

   Attributes:
       id: Primary key
       user_id: Foreign key to the user who uploaded the file
       original_filename: Original name of the uploaded file
       stored_filename: Unique name used in storage
       file_size: Size of the file in bytes
       mime_type: MIME type of the file
       bucket_name: MinIO bucket where file is stored
       status: Current processing status
       error_message: Error details if status is FAILED
       upload_date: Timestamp of file upload
       processed_date: Timestamp of processing completion
       user: Relationship to User model
   """
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False, unique=True, index=True)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)
    bucket_name = Column(String(100), nullable=False)

    status = Column(
        SQLEnum(FileStatus),
        default=FileStatus.PENDING,
        nullable=False,
        index=True
    )
    error_message = Column(String(500), nullable=True)
    parsed_title = Column(String(255), nullable=True)
    parsed_author = Column(String(255), nullable=True)

    upload_date = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
        index=True
    )
    processed_date = Column(TIMESTAMP(timezone=True), nullable=True)

    user = relationship("User", back_populates="files")
    chapters = relationship("Chapter", back_populates="file", cascade="all, delete-orphan")

    def __repr__(self):
        return (
            f"<File(id={self.id}, filename={self.original_filename}, "
            f"status={self.status}, user_id={self.user_id})>"
        )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "original_filename": self.original_filename,
            "stored_filename": self.stored_filename,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "bucket_name": self.bucket_name,
            "status": self.status,
            "error_message": self.error_message,
            "parsed_title": self.parsed_title,
            "parsed_author": self.parsed_author,
            "upload_date": self.upload_date,
            "processed_date": self.processed_date
        }
