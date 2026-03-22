import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.requests import Request

from core.database import get_db_session
from core.session import get_session_token, sessions
from models import User, Chapter
from schemas.reading_history import ReadingHistoryUpdate, ReadingHistoryOut, HistoryListResponse
from services.auth import AuthService
from services.files import FileService
from services.history import HistoryService

logger = logging.getLogger(__name__)
router = APIRouter()


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


@router.post(
    "/{file_id}",
    response_model=ReadingHistoryOut,
    status_code=status.HTTP_200_OK,
    summary="Upsert listening progress for a file",
    tags=["history"],
)
async def upsert_history(
    file_id: int,
    body: ReadingHistoryUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user_dependency),
) -> ReadingHistoryOut:
    """Save or update the current user's playback position for a file."""
    file_record = await FileService.get_file_by_id(db, file_id, current_user.id)
    if not file_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    if body.chapter_id is not None:
        result = await db.execute(select(Chapter).where(Chapter.id == body.chapter_id))
        chapter = result.scalar_one_or_none()
        if not chapter or chapter.file_id != file_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="chapter_id does not belong to this file",
            )

    record = await HistoryService.upsert_progress(
        db=db,
        user_id=current_user.id,
        file_id=file_id,
        chapter_id=body.chapter_id,
        position_seconds=body.position_seconds,
    )
    return ReadingHistoryOut.model_validate(record)


@router.get(
    "/",
    response_model=HistoryListResponse,
    status_code=status.HTTP_200_OK,
    summary="List current user's listening history",
    tags=["history"],
)
async def list_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user_dependency),
) -> HistoryListResponse:
    """Return paginated listening history for the current user."""
    skip = (page - 1) * page_size
    records, total = await HistoryService.get_user_history(db=db, user_id=current_user.id, skip=skip, limit=page_size)
    return HistoryListResponse(
        history=[ReadingHistoryOut.model_validate(r) for r in records],
        total=total,
        page=page,
        page_size=page_size,
    )
