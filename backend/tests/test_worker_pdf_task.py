from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from models import User
from models.chapter import Chapter
from models.file import File, FileStatus
from worker.tasks import AUDIO_BUCKET, _mark_pdf_failed, _process_pdf_async, _process_tts_async


class FakeObjectResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload
        self.closed = False
        self.released = False

    def read(self) -> bytes:
        return self._payload

    def close(self) -> None:
        self.closed = True

    def release_conn(self) -> None:
        self.released = True


class FakeMinioClient:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.uploaded: list[tuple[str, str, int, str]] = []

    async def get_file(self, bucket_name: str, object_name: str) -> FakeObjectResponse:
        return FakeObjectResponse(self.payload)

    async def upload_file(
        self,
        bucket_name: str,
        object_name: str,
        file_data: bytes,
        file_size: int,
        content_type: str,
    ) -> str:
        self.uploaded.append((bucket_name, object_name, file_size, content_type))
        return object_name


@pytest.mark.asyncio
async def test_process_pdf_async_marks_file_completed_and_saves_chapters(
    monkeypatch: pytest.MonkeyPatch,
    async_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with async_session_factory() as session:
        user = User(email="worker-success@example.com", hashed_password="hash", is_active=True)
        session.add(user)
        await session.commit()
        await session.refresh(user)

        file_record = File(
            user_id=user.id,
            original_filename="book.pdf",
            stored_filename="stored_book.pdf",
            file_size=1234,
            mime_type="application/pdf",
            bucket_name="raw-pdf-uploads",
            status=FileStatus.PENDING,
        )
        session.add(file_record)
        await session.commit()
        await session.refresh(file_record)
        file_id = file_record.id

    monkeypatch.setattr("worker.tasks.async_session_maker", async_session_factory)
    monkeypatch.setattr("worker.tasks.get_minio_client", lambda: FakeMinioClient(b"%PDF-1.4 data"))

    async def fake_parse_and_store(db, file_record, pdf_bytes):
        db.add(
            Chapter(
                file_id=file_record.id,
                chapter_index=1,
                title="Chapter 1",
                content="Alpha",
                start_page=1,
                end_page=1,
            )
        )
        db.add(
            Chapter(
                file_id=file_record.id,
                chapter_index=2,
                title="Chapter 2",
                content="Beta",
                start_page=2,
                end_page=2,
            )
        )
        await db.commit()
        return 2

    monkeypatch.setattr("worker.tasks.PdfParsingService.parse_and_store", fake_parse_and_store)
    delay_calls: list[tuple[int, int]] = []

    def fake_delay(file_id_value: int, chapter_id_value: int):
        delay_calls.append((file_id_value, chapter_id_value))

    monkeypatch.setattr("worker.tasks.process_tts.delay", fake_delay)

    result = await _process_pdf_async(file_id=file_id, task_id="task-123")

    assert result["task_id"] == "task-123"
    assert result["file_id"] == file_id
    assert result["status"] == "processing"
    assert result["chapter_count"] == 2
    assert result["queued_tts_jobs"] == 2
    assert len(delay_calls) == 2
    assert all(call[0] == file_id for call in delay_calls)

    async with async_session_factory() as verify_session:
        persisted_file = await verify_session.get(File, file_id)
        assert persisted_file is not None
        assert persisted_file.status == FileStatus.PROCESSING
        assert persisted_file.processed_date is None
        assert persisted_file.error_message is None


@pytest.mark.asyncio
async def test_mark_pdf_failed_sets_status_and_error_message(
    monkeypatch: pytest.MonkeyPatch,
    async_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with async_session_factory() as session:
        user = User(email="worker-failed@example.com", hashed_password="hash", is_active=True)
        session.add(user)
        await session.commit()
        await session.refresh(user)

        file_record = File(
            user_id=user.id,
            original_filename="broken.pdf",
            stored_filename="stored_broken.pdf",
            file_size=1234,
            mime_type="application/pdf",
            bucket_name="raw-pdf-uploads",
            status=FileStatus.PENDING,
        )
        session.add(file_record)
        await session.commit()
        await session.refresh(file_record)
        file_id = file_record.id

    monkeypatch.setattr("worker.tasks.async_session_maker", async_session_factory)

    await _mark_pdf_failed(file_id=file_id, error="parse failed")

    async with async_session_factory() as verify_session:
        persisted_file = await verify_session.get(File, file_id)
        assert persisted_file is not None
        assert persisted_file.status == FileStatus.FAILED
        assert persisted_file.error_message == "parse failed"
        assert persisted_file.processed_date is not None


@pytest.mark.asyncio
async def test_process_tts_async_uploads_audio_and_marks_file_completed(
    monkeypatch: pytest.MonkeyPatch,
    async_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with async_session_factory() as session:
        user = User(email="worker-tts@example.com", hashed_password="hash", is_active=True)
        session.add(user)
        await session.commit()
        await session.refresh(user)

        file_record = File(
            user_id=user.id,
            original_filename="tts.pdf",
            stored_filename="stored_tts.pdf",
            file_size=1234,
            mime_type="application/pdf",
            bucket_name="raw-pdf-uploads",
            status=FileStatus.PROCESSING,
        )
        session.add(file_record)
        await session.commit()
        await session.refresh(file_record)

        chapter = Chapter(
            file_id=file_record.id,
            chapter_index=1,
            title="Chapter 1",
            content="Audio content",
            start_page=1,
            end_page=1,
        )
        session.add(chapter)
        await session.commit()
        await session.refresh(chapter)
        file_id = file_record.id
        chapter_id = chapter.id

    fake_minio = FakeMinioClient(b"")
    monkeypatch.setattr("worker.tasks.async_session_maker", async_session_factory)
    monkeypatch.setattr("worker.tasks.get_minio_client", lambda: fake_minio)
    monkeypatch.setattr(
        "worker.tasks.CoquiTTSService.synthesize",
        AsyncMock(return_value=b"RIFF\x00\x00\x00\x00WAVEfmt "),
    )

    result = await _process_tts_async(file_id=file_id, chapter_id=chapter_id, task_id="tts-task")

    assert result["task_id"] == "tts-task"
    assert result["file_id"] == file_id
    assert result["chapter_id"] == chapter_id
    assert result["remaining_chapters"] == 0
    assert result["status"] == "completed"
    assert fake_minio.uploaded
    assert fake_minio.uploaded[0][0] == AUDIO_BUCKET
    assert fake_minio.uploaded[0][3] == "audio/wav"

    async with async_session_factory() as verify_session:
        persisted_file = await verify_session.get(File, file_id)
        persisted_chapter = await verify_session.get(Chapter, chapter_id)
        assert persisted_file is not None
        assert persisted_chapter is not None
        assert persisted_file.status == FileStatus.COMPLETED
        assert persisted_file.processed_date is not None
        assert persisted_chapter.audio_bucket_name == AUDIO_BUCKET
        assert persisted_chapter.audio_object_name is not None
