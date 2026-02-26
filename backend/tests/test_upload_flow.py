from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.session import SESSION_COOKIE_NAME
from models import User
from models.file import File, FileStatus
from services.files import FileService


class FakeMinioClient:
    def __init__(self) -> None:
        self.uploaded: list[tuple[str, str, int, str]] = []
        self.deleted: list[tuple[str, str]] = []

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

    async def delete_file(self, bucket_name: str, object_name: str) -> bool:
        self.deleted.append((bucket_name, object_name))
        return True


async def create_user(
    session_factory: async_sessionmaker[AsyncSession],
    email: str = "user@example.com",
) -> User:
    async with session_factory() as session:
        user = User(email=email, hashed_password="hash", is_active=True)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


def authenticate_client(client, session_store: dict, user: User) -> None:
    token = "test-session-token"
    session_store[token] = {"user_id": user.id, "email": user.email}
    client.cookies.set(SESSION_COOKIE_NAME, token)


@pytest.mark.asyncio
async def test_upload_requires_authentication(client) -> None:
    response = client.post(
        "/files/upload_file",
        files={"file": ("doc.pdf", b"%PDF-1.4 test", "application/pdf")},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_upload_success_creates_db_record(
    client,
    async_session_factory: async_sessionmaker[AsyncSession],
    session_store: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_minio = FakeMinioClient()
    monkeypatch.setattr("services.files.get_minio_client", lambda: fake_minio)

    user = await create_user(async_session_factory)
    authenticate_client(client, session_store, user)

    response = client.post(
        "/files/upload_file",
        files={"file": ("doc.pdf", b"%PDF-1.4 content", "application/pdf")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["original_filename"] == "doc.pdf"
    assert payload["mime_type"] == "application/pdf"
    assert payload["status"] == "pending"
    assert "upload_date" in payload
    assert fake_minio.uploaded

    async with async_session_factory() as session:
        result = await session.execute(select(File))
        files = result.scalars().all()
        assert len(files) == 1
        assert files[0].original_filename == "doc.pdf"
        assert files[0].user_id == user.id


@pytest.mark.asyncio
async def test_upload_rejects_large_files(
    client,
    async_session_factory: async_sessionmaker[AsyncSession],
    session_store: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_minio = FakeMinioClient()
    monkeypatch.setattr("services.files.get_minio_client", lambda: fake_minio)
    monkeypatch.setattr("services.files.MAX_FILE_SIZE", 1024)

    user = await create_user(async_session_factory, email="large@example.com")
    authenticate_client(client, session_store, user)

    response = client.post(
        "/files/upload_file",
        files={"file": ("big.pdf", b"a" * 2048, "application/pdf")},
    )

    assert response.status_code == 400
    assert "Maximum size" in response.json()["detail"]
    assert not fake_minio.uploaded


@pytest.mark.asyncio
async def test_upload_rejects_wrong_mime_type(
    client,
    async_session_factory: async_sessionmaker[AsyncSession],
    session_store: dict,
) -> None:
    user = await create_user(async_session_factory, email="mime@example.com")
    authenticate_client(client, session_store, user)

    response = client.post(
        "/files/upload_file",
        files={"file": ("doc.pdf", b"%PDF-1.4 content", "text/plain")},
    )

    assert response.status_code == 400
    assert "Invalid MIME type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_duplicate_check_errors_return_server_error(
    async_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    class BrokenSession:
        async def execute(self, *args, **kwargs):
            raise RuntimeError("db down")

    with pytest.raises(HTTPException) as exc:
        await FileService.check_duplicate_file(
            db=BrokenSession(),
            user_id=1,
            original_filename="doc.pdf",
        )

    assert exc.value.status_code == 500
    assert exc.value.detail == "Failed to validate duplicate file"


@pytest.mark.asyncio
async def test_upload_cleans_up_object_when_db_create_fails(
    client,
    async_session_factory: async_sessionmaker[AsyncSession],
    session_store: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_minio = FakeMinioClient()
    monkeypatch.setattr("services.files.get_minio_client", lambda: fake_minio)
    cleanup_mock = AsyncMock()
    monkeypatch.setattr(FileService, "delete_uploaded_file", cleanup_mock)
    monkeypatch.setattr(
        FileService,
        "create_file_record",
        AsyncMock(side_effect=HTTPException(status_code=500, detail="db error")),
    )

    user = await create_user(async_session_factory, email="cleanup@example.com")
    authenticate_client(client, session_store, user)

    response = client.post(
        "/files/upload_file",
        files={"file": ("doc.pdf", b"%PDF-1.4 content", "application/pdf")},
    )

    assert response.status_code == 500
    cleanup_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_endpoint_returns_integer_total(
    client,
    async_session_factory: async_sessionmaker[AsyncSession],
    session_store: dict,
) -> None:
    user = await create_user(async_session_factory, email="list@example.com")
    authenticate_client(client, session_store, user)

    async with async_session_factory() as session:
        file_record = File(
            user_id=user.id,
            original_filename="doc.pdf",
            stored_filename="stored.pdf",
            file_size=1234,
            mime_type="application/pdf",
            bucket_name="raw-pdf-uploads",
            status=FileStatus.PENDING,
            upload_date=datetime.now(timezone.utc),
        )
        session.add(file_record)
        await session.commit()

    response = client.get("/files/list")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert isinstance(payload["total"], int)
