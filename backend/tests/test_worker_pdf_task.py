from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from models import User
from models.file import File, FileStatus
from worker.tasks import _mark_pdf_failed, _process_pdf_async


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

    async def get_file(self, bucket_name: str, object_name: str) -> FakeObjectResponse:
        return FakeObjectResponse(self.payload)


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
    parse_mock = AsyncMock(return_value=2)
    monkeypatch.setattr("worker.tasks.PdfParsingService.parse_and_store", parse_mock)

    result = await _process_pdf_async(file_id=file_id, task_id="task-123")

    assert result["task_id"] == "task-123"
    assert result["file_id"] == file_id
    assert result["status"] == "completed"
    assert result["chapter_count"] == 2

    async with async_session_factory() as verify_session:
        persisted_file = await verify_session.get(File, file_id)
        assert persisted_file is not None
        assert persisted_file.status == FileStatus.COMPLETED
        assert persisted_file.processed_date is not None
        assert persisted_file.error_message is None

    parse_mock.assert_awaited_once()


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
