"""
Celery tasks for async processing.
Contains task definitions for TTS generation, PDF processing, etc.
"""
import asyncio
import datetime
import logging
import time
from typing import Dict, Any

from billiard.exceptions import SoftTimeLimitExceeded
from celery import Task

from core.database import async_session_maker
from core.minio import get_minio_client
from models.file import File, FileStatus
from services.pdf_parser import PdfParsingService
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


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
        text: str,
        voice: str = "default",
        language: str = "en",
        options: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Process text-to-speech conversion asynchronously.

    Args:
        text: Text to convert to speech
        voice: Voice profile to use
        language: Language code
        options: Additional TTS options

    Returns:
        Task result with file information

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        :param options:
        :param language:
        :param voice:
        :param text:
        :param self:
    """
    try:
        print(f"🎤 Processing TTS task {self.request.id}")
        print(f"📝 Text length: {len(text)} characters")
        print(f"🗣️ Voice: {voice}, Language: {language}")

        # TODO: Implement actual TTS processing
        # 1. Validate input text
        # 2. Connect to TTS service/library
        # 3. Generate audio file
        # 4. Upload to MinIO storage
        # 5. Return file metadata

        # Simulate processing time
        time.sleep(5)

        result = {
            "task_id": self.request.id,
            "status": "completed",
            "text": text[:100] + "..." if len(text) > 100 else text,
            "voice": voice,
            "language": language,
            "audio_file": f"tts_{self.request.id}.mp3",
            "duration": 10, # placeholder
            "file_size_bytes": 1024 * 100, # placeholder
            "storage_url": f"minio://tts-files/audio/{self.request.id}.mp3"
        }

        return result

    except SoftTimeLimitExceeded:
        print(f"⏱️ Task {self.request.id} exceeded time limit")
        raise
    except Exception as e:
        print(f"❌ Error processing TTS: {e}")
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

        file_record.status = FileStatus.COMPLETED
        file_record.error_message = None
        file_record.processed_date = datetime.datetime.now(datetime.UTC)
        await db.commit()
        await db.refresh(file_record)

        logger.info(
            "PDF processing completed",
            extra={
                "file_id": file_id,
                "chapter_count": chapter_count,
                "status": file_record.status.value,
            },
        )

        return {
            "task_id": task_id,
            "file_id": file_id,
            "status": file_record.status.value,
            "chapter_count": chapter_count,
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
