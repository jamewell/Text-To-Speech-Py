"""
File service for handling file upload operations.

This module provides business logic for file validation, storage,
and metadata management with comprehensive logging.
"""
import datetime
import logging
import time
import uuid
from pathlib import Path
from typing import Optional

from fastapi import UploadFile, HTTPException
from minio import S3Error
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status

from core.minio import get_minio_client
from models.file import File, FileStatus, FileVisibility

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 50 * 1024 * 1024 #50mb
ALLOWED_MIME_TYPES = {"application/pdf"}
ALLOWED_EXTENSIONS = {".pdf"}
RAW_PDF_BUCKET = "raw-pdf-uploads"

class FileValidationError(Exception):
    """Custom exception for file validation errors."""
    pass


class FileService:

    @staticmethod
    def validate_pdf_files(file: UploadFile)-> dict:
        """
        Validate uploaded PDF file
        :param file: The uploaded
        :return:
        """

        validation_start = time.time()

        logger.info(
            "starting file validation",
            extra={
                "original_filename": file.filename,
                "content_type": file.content_type,
                "headers": dict(file.headers) if hasattr(file, 'headers') else {}
            }
        )

        if not file.filename:
            logger.warning(
                "File validation failed: missing filename",
                extra={"content_type": file.content_type}
            )
            raise FileValidationError("Filename is required")

        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            logger.warning(
                "File validation failed: invalid extension",
                extra={
                    "original_filename": file.filename,
                    "content_type": file.content_type,
                    "allowed_types": list(ALLOWED_MIME_TYPES)
                }
            )
            raise FileValidationError(
                f"Invalid file type, Allowed: {', '.join(ALLOWED_MIME_TYPES)}"
            )

        if file.content_type not in ALLOWED_MIME_TYPES:
            logger.warning(
                "File validation failed: invalid mime type",
                extra={
                    "original_filename": file.filename,
                    "content_type": file.content_type,
                    "allowed_types": list(ALLOWED_MIME_TYPES)
                }
            )
            raise FileValidationError(
                f"Invalid MIME type, Allowed: {', '.join(ALLOWED_MIME_TYPES)}"
            )

        file_size = getattr(file, "size", None)

        validation_duration = time.time() - validation_start

        logger.info(
            "File validation successful",
            extra={
                "original_filename": file.filename,
                "content_type": file.content_type,
                "file_size": file_size,
                "validation_duration_ms": round(validation_duration * 1000, 2)
            }
        )

        return {
            "original_filename": file.filename,
            "content_type": file.content_type,
            "file_size": file_size
        }

    @staticmethod
    def generate_unique_filename(user_id: int, original_filename: str)-> str:
        """
        Generate a unique filename for storage.

        Args:
            user_id: ID of the user uploading the file
            original_filename: Original name of the file

        Returns:
            str: Unique filename with format: user_{id}_{timestamp}_{uuid}.{ext}
        """

        timestamp = int(datetime.datetime.now(datetime.UTC).timestamp())
        unique_id = uuid.uuid4().hex[:8]
        file_ext = Path(original_filename).suffix.lower()

        unique_filename = f"user_{user_id}_{timestamp}_{unique_id}{file_ext}"

        logger.debug(
            "General unique filename",
            extra={
                "user_id": user_id,
                "original_filename": original_filename,
                "unique_filename": unique_filename
            }
        )

        return unique_filename

    @staticmethod
    async def save_uploaded_file(
            file: UploadFile,
            user_id: int,
            stored_filename: str
    )-> tuple[str, int]:
        """
        Save uploaded file to MinIO storage.

        Args:
            file: The uploaded file object
            user_id: ID of the user uploading the file
            stored_filename: Unique filename for storage

        Returns:
            str: Stored filename

        Raises:
            HTTPException: If storage operation fails
        """

        upload_start = time.time()
        correlation_id = uuid.uuid4().hex[:12]

        logger.info(
            "Starting file upload to MinIO",
            extra={
                "user_id": user_id,
                "original_filename": file.filename,
                "stored_filename": stored_filename,
                "bucket": RAW_PDF_BUCKET,
                "correlation_id": correlation_id,
            }
        )

        minio_client = get_minio_client()

        try:
            await file.seek(0)
            chunks: list[bytes] = []
            file_size = 0
            chunk_size = 1024 * 1024

            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                file_size += len(chunk)
                if file_size > MAX_FILE_SIZE:
                    raise FileValidationError(
                        f"File too large. Maximum size: {MAX_FILE_SIZE / (1024 * 1024):.0f}MB"
                    )
                chunks.append(chunk)

            if file_size == 0:
                raise FileValidationError("File is empty")

            file_content = b"".join(chunks)

            logger.debug(
                "File content read",
                extra={
                    "file_size": file_size,
                    "correlation_id": correlation_id
                }
            )

            await minio_client.upload_file(
                bucket_name=RAW_PDF_BUCKET,
                object_name=stored_filename,
                file_data=file_content,
                file_size=file_size,
                content_type=file.content_type
            )

            upload_duration = time.time() - upload_start

            logger.info(
                "File uploaded to MinIO successfully",
                extra={
                    "user_id": user_id,
                    "stored_filename": stored_filename,
                    "file_size": file_size,
                    "bucket": RAW_PDF_BUCKET,
                    "upload_duration_ms": round(upload_duration * 1000 * 12),
                    "correlation_id": correlation_id,
                }
            )

            await file.seek(0)

            return stored_filename, file_size

        except S3Error as e:
            logger.error(
                "MinIO upload failed",
                extra={
                    "user_id": user_id,
                    "stored_filename": stored_filename,
                    "bucket": RAW_PDF_BUCKET,
                    "error": str(e),
                    "error_code": e.code,
                    "correlation_id": correlation_id
                },
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred during upload"
            )

    @staticmethod
    async def create_file_record(
            db: AsyncSession,
            user_id: int,
            original_filename: str,
            stored_filename: str,
            file_size: int,
            mime_type: str,
            visibility: FileVisibility = FileVisibility.PRIVATE,
    ) -> File:
        """
        Create a database record for the uploaded file.

        Args:
            db: Database session
            user_id: ID of the user uploading the file
            original_filename: Original name of the file
            stored_filename: Unique name used in storage
            file_size: Size of the file in bytes
            mime_type: MIME type of the file

        Returns:
            File: Created file record

        Raises:
            HTTPException: If database operation fails
        """

        correlation_id = uuid.uuid4().hex[:12]

        logger.info(
            "Creating file database record",
            extra={
                "user_id": user_id,
                "original_filename": original_filename,
                "stored_filename": stored_filename,
                "file_size": file_size,
                "correlation_id": correlation_id,
            }
        )

        try:
            file_record = File(
                user_id=user_id,
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_size=file_size,
                mime_type=mime_type,
                bucket_name=RAW_PDF_BUCKET,
                status=FileStatus.PENDING,
                visibility=visibility,
            )

            db.add(file_record)
            await db.commit()
            await db.refresh(file_record)

            logger.info(
                "File record created successfully",
                extra={
                    "file_id": file_record.id,
                    "user_id": user_id,
                    "stored_filename": stored_filename,
                    "status": file_record.status.value,
                    "correlation_id": correlation_id
                }
            )

            return file_record

        except Exception as e:
            await db.rollback()

            logger.error(
                "Failed to create file database record",
                extra={
                    "user_id": user_id,
                    "stored_filename": stored_filename,
                    "error": str(e),
                    "correlation_id": correlation_id
                },
                exc_info=True
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save file metadata"
            )

    @staticmethod
    async def check_duplicate_file(
            db: AsyncSession,
            user_id: int,
            original_filename: str
    ) -> Optional[File]:
        """
        Check if a file with the same name already exists for this user.

        Args:
            db: Database session
            user_id: ID of the user
            original_filename: Original name of the file to check

        Returns:
            Optional[File]: Existing file record if found, None otherwise
        """

        try:
            result = await db.execute(
                select(File)
                .where(and_(File.user_id == user_id))
                .where(and_(File.original_filename == original_filename))
                .where(and_(File.status != FileStatus.FAILED))
                .order_by(File.upload_date.desc())
                .limit(1)
            )

            existing_file = result.scalar_one_or_none()

            if existing_file:
                logger.info(
                    "Duplicate file detected",
                    extra={
                        "user_id": user_id,
                        "original_filename": original_filename,
                        "existing_file_id": existing_file.id,
                        "upload_date": existing_file.upload_date.isoformat()
                    }
                )

            return existing_file

        except Exception as e:
            logger.error(
                "Failed to check for duplicate file",
                extra={
                    "user_id": user_id,
                    "original_filename": original_filename,
                    "error": str(e)
                },
                exc_info=True
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to validate duplicate file"
            )

    @staticmethod
    async def delete_uploaded_file(stored_filename: str) -> None:
        minio_client = get_minio_client()
        try:
            await minio_client.delete_file(
                bucket_name=RAW_PDF_BUCKET,
                object_name=stored_filename,
            )
        except Exception:
            logger.exception(
                "Failed to cleanup uploaded object after database failure",
                extra={"stored_filename": stored_filename, "bucket": RAW_PDF_BUCKET}
            )

    @staticmethod
    async def get_user_files(
            db: AsyncSession,
            user_id: int,
            skip: int = 0,
            limit: int = 20
    )-> list[File]:
        """
        Get files uploaded by a specific user.

        Args:
            db: Database session
            user_id: ID of the user
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return

        Returns:
            list[File]: List of file records
        """

        try:
            result = await db.execute(
                select(File)
                .options(selectinload(File.chapters))
                .where(and_(File.user_id == user_id))
                .order_by(File.upload_date.desc())
                .offset(skip)
                .limit(limit)
            )

            files = list(result.scalars().all())

            logger.info(
                "Retrieved user files",
                extra={
                    "user_id": user_id,
                    "count": len(files),
                    "skip": skip,
                    "limit": limit,
                }
            )

            return files

        except Exception as e:
            logger.error(
                "Failed to retrieve user files",
                extra={
                    "user_id": user_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise

    @staticmethod
    async def get_file_by_id(
            db: AsyncSession,
            file_id: int,
            user_id: int,
    ) -> Optional[File]:
        """
        Get a specific file by ID for the owning user, with chapters eager-loaded.

        Returns the file if:
          - The file exists AND belongs to user_id, OR
          - The file exists AND is public

        Args:
            db: Database session
            file_id: ID of the file
            user_id: ID of the requesting user

        Returns:
            Optional[File]: File record if found and accessible, None otherwise
        """
        try:
            result = await db.execute(
                select(File)
                .options(selectinload(File.chapters))
                .where(
                    File.id == file_id,
                    (File.user_id == user_id) | (File.visibility == FileVisibility.PUBLIC),
                )
                .limit(1)
            )

            file_record = result.scalar_one_or_none()

            if file_record:
                logger.debug(
                    "File retrieved",
                    extra={"file_id": file_id, "user_id": user_id}
                )
            else:
                logger.warning(
                    "File not found or unauthorized",
                    extra={"file_id": file_id, "user_id": user_id}
                )

            return file_record

        except Exception as e:
            logger.error(
                "Failed to retrieve file",
                extra={"file_id": file_id, "user_id": user_id, "error": str(e)}
            )
            raise

    @staticmethod
    async def get_file_by_owner(
            db: AsyncSession,
            file_id: int,
            user_id: int,
    ) -> Optional[File]:
        """
        Fetch a file only if user_id is the owner. Used for mutating operations
        (delete, update) where visibility must never grant access to non-owners.
        """
        try:
            result = await db.execute(
                select(File)
                .options(selectinload(File.chapters))
                .where(File.id == file_id, File.user_id == user_id)
                .limit(1)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                "Failed to retrieve file (owner check)",
                extra={"file_id": file_id, "user_id": user_id, "error": str(e)}
            )
            raise

    @staticmethod
    async def delete_file(
            db: AsyncSession,
            file_id: int,
            user_id: int,
    )-> bool:
        """
        Delete a file and its metadata.

        Args:
            db: Database session
            file_id: ID of the file to delete
            user_id: ID of the user (for authorization)

        Returns:
            bool: True if deleted successfully

        Raises:
            HTTPException: If file not found or deletion fails
        """
        correlation_id = uuid.uuid4().hex[:12]

        logger.info(
            "Starting file deletion",
            extra={
                "file_id": file_id,
                "user_id": user_id,
                "correlation_id": correlation_id
            }
        )

        file_record = await FileService.get_file_by_owner(db, file_id, user_id)

        if not file_record:
            logger.warning(
                "File deletion failed: file not found",
                extra={
                    "file_id": file_id,
                    "user_id": user_id,
                    "correlation_id": correlation_id
                }
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )

        minio_client = get_minio_client()

        try:
            await minio_client.delete_file(
                bucket_name=file_record.bucket_name,
                object_name=file_record.stored_filename,
            )

            await db.delete(file_record)
            await db.commit()

            logger.info(
                "File deleted successfully",
                extra={
                    "file_id": file_id,
                    "user_id": user_id,
                    "stored_filename": file_record.stored_filename,
                    "correlation_id": correlation_id
                }
            )

            return True

        except Exception as e:
            await db.rollback()

            logger.error(
                "Failed to delete file",
                extra={
                    "file_id": file_id,
                    "user_id": user_id,
                    "error": str(e),
                    "correlation_id": correlation_id
                },
                exc_info=True
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete file"
            )


        
