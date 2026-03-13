"""
Celery tasks for async processing.
Contains task definitions for TTS generation, PDF processing, etc.
"""
import asyncio
import datetime
import logging
from typing import Dict, Any

from billiard.exceptions import SoftTimeLimitExceeded
from celery import Task
from sqlalchemy import select, func

from core.database import async_session_maker
from core.minio import get_minio_client
from models.chapter import Chapter
from models.file import File, FileStatus
from services.pdf_parser import PdfParsingService
from services.tts import CoquiTTSService
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)
AUDIO_BUCKET = "completed-files"


class BaseTask(Task):
    """
    Base task class with error handling and logging.
    All tasks should inherit from this class.
    """

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handler called when task fails."""
        print(f"❌ Task {self.name} [{task_id}] failed: {exc}")
        # TODO: Add error logging to database or external service
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        """Handler called when task succeeds."""
        print(f"✅ Task {self.name} [{task_id}] completed successfully")
        # TODO: Add success logging to database
        super().on_success(retval, task_id, args, kwargs)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handler called when task is retried."""
        print(f"🔄 Task {self.name} [{task_id}] retrying due to: {exc}")
        super().on_retry(exc, task_id, args, kwargs, einfo)

@celery_app.task(
    name="worker.tasks.health_check",
    base=BaseTask,
    bind=True
)
def health_check(self) -> Dict[str, str]:
    """
    Simple health check task to verify Celery is working.

    Returns:
        Status message with task info
    """
    return {
        "status": "healthy",
        "task_id": self.request.id,
        "task_name": self.name,
        "message": "Celery worker is operational"
    }

@celery_app.task(
    name="worker.tasks.process_tts",
    base=BaseTask,
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def process_tts(
        self,
        file_id: int,
        chapter_id: int,
) -> Dict[str, Any]:
    """
    Process text-to-speech conversion asynchronously.

    Args:
        file_id: File record ID.
        chapter_id: Chapter record ID to convert.

    Returns:
        Task result with file information

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
    """
    try:
        print(f"🎤 Processing TTS task {self.request.id} for file_id={file_id}, chapter_id={chapter_id}")
        return asyncio.run(
            _process_tts_async(
                file_id=file_id,
                chapter_id=chapter_id,
                task_id=self.request.id,
            )
        )

    except SoftTimeLimitExceeded:
        print(f"⏱️ Task {self.request.id} exceeded time limit")
        raise
    except Exception as e:
        if self.request.retries >= self.max_retries:
            asyncio.run(_mark_file_failed(file_id=file_id, error=str(e)))
        print(f"❌ Error processing TTS for file_id={file_id}, chapter_id={chapter_id}: {e}")
        raise self.retry(e=e)


@celery_app.task(
    name="worker.tasks.process_pdf",
    base=BaseTask,
    bind=True,
    max_retries=3
)
def process_pdf(
        self,
        file_id: int
) -> Dict[str, Any]:
    """
    Process PDF file asynchronously.

    Args:
        file_id: Database ID for the uploaded file.

    Returns:
        Task result with extracted content
    """
    try:
        print(f"📄 Processing PDF task {self.request.id} for file_id={file_id}")
        return asyncio.run(_process_pdf_async(file_id=file_id, task_id=self.request.id))

    except Exception as exc:
        asyncio.run(_mark_pdf_failed(file_id=file_id, error=str(exc)))
        print(f"❌ Error processing PDF for file_id={file_id}: {exc}")
        raise self.retry(exc=exc)


async def _process_pdf_async(file_id: int, task_id: str | None) -> Dict[str, Any]:
    async with async_session_maker() as db:
        file_record = await db.get(File, file_id)
        if not file_record:
            raise ValueError(f"File with id={file_id} not found")

        file_record.status = FileStatus.PROCESSING
        file_record.error_message = None
        await db.commit()
        await db.refresh(file_record)

        minio_client = get_minio_client()
        response = await minio_client.get_file(
            bucket_name=file_record.bucket_name,
            object_name=file_record.stored_filename,
        )

        try:
            pdf_bytes = response.read()
        finally:
            response.close()
            response.release_conn()

        chapter_count = await PdfParsingService.parse_and_store(
            db=db,
            file_record=file_record,
            pdf_bytes=pdf_bytes,
        )

        chapter_result = await db.execute(
            select(Chapter.id).where(Chapter.file_id == file_record.id).order_by(Chapter.chapter_index.asc())
        )
        chapter_ids = [row[0] for row in chapter_result.all()]

        for chapter_id in chapter_ids:
            process_tts.delay(file_record.id, chapter_id)

        file_record.status = FileStatus.PROCESSING
        file_record.error_message = None
        file_record.processed_date = None
        await db.commit()
        await db.refresh(file_record)

        logger.info(
            "PDF processing completed",
            extra={
                "file_id": file_id,
                "chapter_count": chapter_count,
                "queued_tts_jobs": len(chapter_ids),
                "status": file_record.status.value,
            },
        )

        return {
            "task_id": task_id,
            "file_id": file_id,
            "status": file_record.status.value,
            "chapter_count": chapter_count,
            "queued_tts_jobs": len(chapter_ids),
        }


async def _mark_pdf_failed(file_id: int, error: str) -> None:
    async with async_session_maker() as db:
        file_record = await db.get(File, file_id)
        if not file_record:
            return

        file_record.status = FileStatus.FAILED
        file_record.error_message = error[:500]
        file_record.processed_date = datetime.datetime.now(datetime.UTC)
        await db.commit()


async def _mark_file_failed(file_id: int, error: str) -> None:
    async with async_session_maker() as db:
        file_record = await db.get(File, file_id)
        if not file_record:
            return

        file_record.status = FileStatus.FAILED
        file_record.error_message = error[:500]
        file_record.processed_date = datetime.datetime.now(datetime.UTC)
        await db.commit()


async def _process_tts_async(file_id: int, chapter_id: int, task_id: str | None) -> Dict[str, Any]:
    async with async_session_maker() as db:
        file_record = await db.get(File, file_id)
        if not file_record:
            raise ValueError(f"File with id={file_id} not found")

        chapter = await db.get(Chapter, chapter_id)
        if not chapter or chapter.file_id != file_id:
            raise ValueError(f"Chapter with id={chapter_id} not found for file_id={file_id}")

        file_record.status = FileStatus.PROCESSING
        file_record.error_message = None

        audio_bytes = await CoquiTTSService.synthesize(chapter.content)
        object_name = f"file_{file_id}/chapter_{chapter.chapter_index}_{chapter.id}.wav"

        minio_client = get_minio_client()
        await minio_client.upload_file(
            bucket_name=AUDIO_BUCKET,
            object_name=object_name,
            file_data=audio_bytes,
            file_size=len(audio_bytes),
            content_type="audio/wav",
        )

        chapter.audio_bucket_name = AUDIO_BUCKET
        chapter.audio_object_name = object_name
        await db.commit()

        remaining_result = await db.execute(
            select(func.count())
            .select_from(Chapter)
            .where(Chapter.file_id == file_id)
            .where(Chapter.audio_object_name.is_(None))
        )
        remaining_count = remaining_result.scalar_one()

        if remaining_count == 0:
            file_record.status = FileStatus.COMPLETED
            file_record.error_message = None
            file_record.processed_date = datetime.datetime.now(datetime.UTC)
            await db.commit()

        return {
            "task_id": task_id,
            "file_id": file_id,
            "chapter_id": chapter_id,
            "remaining_chapters": remaining_count,
            "status": file_record.status.value,
            "audio_object_name": object_name,
        }


@celery_app.task(
    name="worker.tasks.cleanup_old_files",
    base=BaseTask,
    bind=True
)
def cleanup_old_files(self, days: int = 7) -> Dict[str, Any]:
    """
    Cleanup old files from storage (periodic task).

    Args:
        days: Remove files older than this many days

    Returns:
        Cleanup statistics
        :param days:
        :param self:
    """
    try:
        print(f"🧹 Running cleanup task {self.request.id}")
        print(f"📅 Removing files older than {days} days")

        # TODO: Implement actual cleanup
        # 1. Connect to MinIO
        # 2. List files with timestamps
        # 3. Delete files older than threshold
        # 4. Update database records
        # 5. Return statistics

        result = {
            "task_id": self.request.id,
            "status": "completed",
            "files_removed": 0,  # Placeholder
            "space_freed_mb": 0,  # Placeholder
            "threshold_days": days
        }

        return result

    except Exception as exc:
        print(f"❌ Error during cleanup: {exc}")
        raise self.retry(exc=exc)
