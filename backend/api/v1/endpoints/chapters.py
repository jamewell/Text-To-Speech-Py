import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.requests import Request

from core.database import get_db_session
from core.minio import get_minio_client, MinIOClient
from core.session import get_session_token, sessions
from models import User, Chapter
from models.file import File as FileModel, FileVisibility
from schemas.chapter import ChapterAudioResponse
from services.auth import AuthService

logger = logging.getLogger(__name__)
router = APIRouter()

PRESIGNED_URL_TTL = timedelta(hours=1)


async def get_current_user_dependency(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> User:
    session_token = get_session_token(request)
    if not session_token or session_token not in sessions:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    session_data = sessions[session_token]
    user = await AuthService.get_current_user_from_session(db, session_data.get("user_id"))
    if not user:
        del sessions[session_token]
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return user


@router.get(
    "/{chapter_id}/audio",
    response_model=ChapterAudioResponse,
    summary="Get presigned audio URL for a chapter",
    description="""
    Returns a time-limited presigned URL that can be used to stream or download
    the generated audio for a specific chapter.

    **Access rules:**
    - Owner can always access their own chapters
    - Non-owners can access chapters whose parent file is set to **public**

    **Returns:**
    - 200: Presigned URL valid for 1 hour
    - 401: Not authenticated
    - 403: Chapter belongs to a private file owned by another user
    - 404: Chapter not found
    - 409: Audio not yet available (TTS not completed)
    """,
    tags=["Chapters"],
)
async def get_chapter_audio(
    chapter_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user_dependency),
    minio: MinIOClient = Depends(get_minio_client),
) -> ChapterAudioResponse:
    logger.info("Chapter audio request", extra={"chapter_id": chapter_id, "user_id": current_user.id})

    # Fetch chapter
    result = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
    chapter = result.scalar_one_or_none()

    if not chapter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")

    # Fetch the parent file to enforce visibility
    file_result = await db.execute(select(FileModel).where(FileModel.id == chapter.file_id))
    file_record = file_result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")

    # Allow access if: owner, or file is public
    is_owner = file_record.user_id == current_user.id
    is_public = file_record.visibility == FileVisibility.PUBLIC

    if not is_owner and not is_public:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Check audio has been generated
    if not chapter.audio_bucket_name or not chapter.audio_object_name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Audio not yet available. Check back once the file has finished processing.",
        )

    url = await minio.generate_presigned_url(
        bucket_name=chapter.audio_bucket_name,
        object_name=chapter.audio_object_name,
        expires=PRESIGNED_URL_TTL,
    )

    logger.info(
        "Presigned audio URL issued",
        extra={
            "chapter_id": chapter_id,
            "file_id": chapter.file_id,
            "user_id": current_user.id,
            "bucket": chapter.audio_bucket_name,
            "object": chapter.audio_object_name,
        },
    )

    return ChapterAudioResponse(
        chapter_id=chapter_id,
        url=url,
        expires_in_seconds=int(PRESIGNED_URL_TTL.total_seconds()),
    )
