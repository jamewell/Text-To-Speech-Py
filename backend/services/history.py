import datetime
import logging
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.reading_history import ReadingHistory

logger = logging.getLogger(__name__)


class HistoryService:

    @staticmethod
    async def upsert_progress(
        db: AsyncSession,
        user_id: int,
        file_id: int,
        chapter_id: Optional[int],
        position_seconds: float,
    ) -> ReadingHistory:
        """Insert or update the listening progress for a user/file pair."""
        try:
            result = await db.execute(
                select(ReadingHistory).where(
                    ReadingHistory.user_id == user_id,
                    ReadingHistory.file_id == file_id,
                )
            )
            record = result.scalar_one_or_none()

            if record:
                record.chapter_id = chapter_id
                record.position_seconds = position_seconds
                record.updated_at = datetime.datetime.now(datetime.UTC)
            else:
                record = ReadingHistory(
                    user_id=user_id,
                    file_id=file_id,
                    chapter_id=chapter_id,
                    position_seconds=position_seconds,
                    updated_at=datetime.datetime.now(datetime.UTC),
                )
                db.add(record)

            await db.commit()
            await db.refresh(record)
            return record

        except Exception:
            await db.rollback()
            logger.exception(
                "Failed to upsert reading history",
                extra={"user_id": user_id, "file_id": file_id},
            )
            raise

    @staticmethod
    async def get_user_history(
        db: AsyncSession,
        user_id: int,
        skip: int,
        limit: int,
    ) -> tuple[list[ReadingHistory], int]:
        """Return paginated listening history for a user, newest first."""
        records_result = await db.execute(
            select(ReadingHistory)
            .where(ReadingHistory.user_id == user_id)
            .order_by(ReadingHistory.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        records = list(records_result.scalars().all())

        count_result = await db.execute(
            select(func.count()).select_from(ReadingHistory).where(ReadingHistory.user_id == user_id)
        )
        total = count_result.scalar_one()

        return records, total
