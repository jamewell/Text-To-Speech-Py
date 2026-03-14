import logging
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Form
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette import status

from core.database import get_db_session
from core.session import get_session_token, sessions
from models import User
from models.file import File as FileModel, FileVisibility
from schemas.file import FileUploadResponse, FileListResponse, FileOut, FileDeleteResponse, FileVisibilityUpdate
from services.auth import AuthService
from services.files import FileService, FileValidationError
from worker.tasks import process_pdf as process_pdf_task

logger = logging.getLogger(__name__)
router = APIRouter()


async def get_current_user_dependency(
        request: Request,
        db: AsyncSession = Depends(get_db_session)
) -> User:
    session_token = get_session_token(request)

    if not session_token or session_token not in sessions:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    session_data = sessions[session_token]
    user_id = session_data.get("user_id")
    user = await AuthService.get_current_user_from_session(db, user_id)
    if not user:
        del sessions[session_token]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    return user


@router.post(
    "/upload_file",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF file",
    description="""
    Upload a PDF file for text-to-speech conversion.

    **Requirements:**
    - File must be a PDF (application/pdf)
    - Maximum file size: 50MB
    - User must be authenticated
    - File name must be unique per user (no duplicates)

    **Process:**
     1. File is validated for type and size
    2. System checks for duplicate filenames
    3. File is stored in MinIO object storage
    4. Metadata is saved to database
    5. File is queued for processing

    **Returns:**
    - 201: File uploaded successfully with metadata
    - 400: Invalid file (wrong type, too large, etc.)
    - 401: User not authenticated
    - 409: File with same name already exists
    - 413: File too large
    - 500: Server error during upload
    """,
    responses={
        201: {
            "description": "File uploaded successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "original_filename": "document.pdf",
                        "stored_filename": "user_1_1698765432_a1b2c3d4.pdf",
                        "file_size": 1048576,
                        "mime_type": "application/pdf",
                        "status": "pending",
                        "upload_date": "2024-10-31T12:00:00Z"
                    }
                }
            }
        },
        400: {
            "description": "Invalid file",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid file type. Allowed: .pdf"
                    }
                }
            }
        },
        413: {
            "description": "File too large",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "File too large. Maximum size: 50MB"
                    }
                }
            }
        },
        409: {
            "description": "Duplicate file",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "File 'document.pdf' already exists. Uploaded on 2024-10-31 12:00:00. Please rename the file or delete the existing one first."
                    }
                }
            }
        }
    },
    tags=["Files"]
)
async def upload_file(
        file: UploadFile = File(..., description="PDF file to upload"),
        visibility: str = Form("private", description="File visibility: 'private' or 'public'"),
        db: AsyncSession = Depends(get_db_session),
        current_user: User = Depends(get_current_user_dependency)
):
    """
    Upload a PDF file for processing.

    This endpoint handles the complete file upload workflow including
    validation, storage, and metadata management.
    """
    request_start = time.time()
    correlation_id = uuid.uuid4().hex[:12]

    logger.info(
        "File upload request initiated",
        extra={
            "user_id": current_user.id,
            "original_filename": file.filename,
            "content_type": file.content_type,
            "correlation_id": correlation_id
        }
    )

    try:
        try:
            visibility_enum = FileVisibility(visibility)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid visibility value '{visibility}'. Allowed: private, public"
            )

        FileService.validate_pdf_files(file)

        existing_file = await FileService.check_duplicate_file(
            db=db,
            user_id=current_user.id,
            original_filename=file.filename
        )

        if existing_file:
            logger.warning(
                "Duplicate file upload attempt",
                extra={
                    "user_id": current_user.id,
                    "original_filename": file.filename,
                    "existing_file_id": existing_file.id,
                    "correlation_id": correlation_id
                }
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"File '{file.filename}' already exists. Uploaded on {existing_file.upload_date.strftime('%Y-%m-%d %H:%M:%S')}. Please rename the file or delete the existing one first."
            )

        stored_filename = FileService.generate_unique_filename(
            current_user.id,
            file.filename
        )

        _, actual_file_size = await FileService.save_uploaded_file(
            file=file,
            user_id=current_user.id,
            stored_filename=stored_filename
        )

        try:
            file_record = await FileService.create_file_record(
                db=db,
                user_id=current_user.id,
                original_filename=file.filename,
                stored_filename=stored_filename,
                file_size=actual_file_size,
                mime_type=file.content_type,
                visibility=visibility_enum,
            )
        except Exception:
            await FileService.delete_uploaded_file(stored_filename)
            raise

        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create file record"
            )

        # Best effort queueing: uploads should still succeed if broker is temporarily unavailable.
        try:
            process_pdf_task.delay(file_record.id)
        except Exception as queue_exc:
            logger.warning(
                "PDF processing task enqueue failed after upload",
                extra={
                    "file_id": file_record.id,
                    "user_id": current_user.id,
                    "error": str(queue_exc),
                    "correlation_id": correlation_id,
                },
            )

        request_duration = time.time() - request_start

        logger.info(
            "File upload completed successfully",
            extra={
                "file_id": file_record.id,
                "user_id": current_user.id,
                "original_filename": file.filename,
                "stored_filename": stored_filename,
                "file_size": actual_file_size,
                "total_duration_ms": round(request_duration * 1000, 2),
                "correlation_id": correlation_id
            }
        )

        return FileUploadResponse(
            id=file_record.id,
            original_filename=file_record.original_filename,
            stored_filename=file_record.stored_filename,
            file_size=file_record.file_size,
            mime_type=file_record.mime_type,
            status=file_record.status.value,
            upload_date=file_record.upload_date
        )

    except FileValidationError as e:
        logger.warning(
            "File upload failed: validation error",
            extra={
                "user_id": current_user.id,
                "original_filename": file.filename,
                "error": str(e),
                "correlation_id": correlation_id
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            "File upload failed: unexpected error",
            extra={
                "user_id": current_user.id,
                "original_filename": file.filename,
                "error": str(e),
                "correlation_id": correlation_id
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An Unexpected error occurred during file upload"
        )


@router.get(
    "/list",
    response_model=FileListResponse,
    summary="List uploaded files",
    description="""
    Get a list of files uploaded by the current user.

    **Query Parameters:**
    - page: Page number (default: 1)
    - page_size: Number of items per page (default: 20, max: 100)

    **Returns:**
    - List of files with metadata
    - Total count of files
    - Pagination information
    """,
    tags=["Files"]
)
async def list_files(
        page: int = Query(1, ge=1, description="Page Number"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page"),
        db: AsyncSession = Depends(get_db_session),
        current_user: User = Depends(get_current_user_dependency)
):
    """List files uploaded by the current user."""

    logger.info(
        "File list request",
        extra={
            "user_id": current_user.id,
            "page": page,
            "page_size": page_size
        }
    )

    try:
        skip = (page - 1) * page_size
        files = await FileService.get_user_files(
            db=db,
            user_id=current_user.id,
            skip=skip,
            limit=page_size
        )

        result = await db.execute(
            select(func.count()).select_from(FileModel).where(and_(FileModel.user_id == current_user.id))
        )
        total = result.scalar_one()

        return FileListResponse(
            files=[FileOut.model_validate(f) for f in files],
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(
            "Failed to list files",
            extra={
                "user_id": current_user.id,
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve file list"
        )


@router.get(
    "/{file_id}",
    response_model=FileOut,
    summary="Get file details",
    description="""
    Get detailed information about a specific file.
    
    **Returns:**
    - 200: File details
    - 404: File not found or not authorized
    """,
    tags=["Files"]
)
async def get_file(
        file_id: int,
        db: AsyncSession = Depends(get_db_session),
        current_user: User = Depends(get_current_user_dependency)
):
    """Get details of a specific file."""

    logger.info(
        "File details request",
        extra={
            "file_id": file_id,
            "user_id": current_user.id
        }
    )

    file_record = await FileService.get_file_by_id(db, file_id, current_user.id)

    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    return FileOut.model_validate(file_record)


@router.delete(
    "/{file_id}",
    response_model=FileDeleteResponse,
    summary="Delete a file",
    description="""
    Delete a file and its metadata.

    **Returns:**
    - 200: File deleted successfully
    - 404: File not found or not authorized
    - 500: Failed to delete file
    """,
    tags=["Files"]
)
async def delete_file(
        file_id: int,
        db: AsyncSession = Depends(get_db_session),
        current_user: User = Depends(get_current_user_dependency)
):
    """Delete a file and its metadata."""

    logger.info(
        "File deletion request",
        extra={
            "file_id": file_id,
            "user_id": current_user.id
        }
    )

    try:
        await FileService.delete_file(db, file_id, current_user.id)

        return FileDeleteResponse(
            message="File deleted successfully",
            file_id=file_id,
            deleted=True
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            "Failed to delete file",
            extra={
                "file_id": file_id,
                "user_id": current_user.id,
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file"
        )


@router.patch(
    "/{file_id}/visibility",
    response_model=FileOut,
    summary="Update file visibility",
    description="""
    Update the visibility of a file (private or public).

    Only the file owner can change visibility.

    **Returns:**
    - 200: Updated file details
    - 404: File not found or not authorized
    - 500: Failed to update file
    """,
    tags=["Files"]
)
async def update_file_visibility(
        file_id: int,
        body: FileVisibilityUpdate,
        db: AsyncSession = Depends(get_db_session),
        current_user: User = Depends(get_current_user_dependency)
):
    """Update visibility of a file (owner only)."""

    logger.info(
        "File visibility update request",
        extra={
            "file_id": file_id,
            "user_id": current_user.id,
            "new_visibility": body.visibility
        }
    )

    try:
        file_record = await FileService.get_file_by_owner(db, file_id, current_user.id)

        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )

        file_record.visibility = FileVisibility(body.visibility)
        await db.commit()
        await db.refresh(file_record)

        return FileOut.model_validate(file_record)

    except HTTPException:
        raise

    except Exception as e:
        await db.rollback()
        logger.error(
            "Failed to update file visibility",
            extra={
                "file_id": file_id,
                "user_id": current_user.id,
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update file visibility"
        )
