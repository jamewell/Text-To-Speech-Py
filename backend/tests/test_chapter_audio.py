"""
Tests for GET /chapters/{chapter_id}/audio access-control rules.

Covers:
- 401 when unauthenticated
- 200 owner can always fetch audio for their own chapter
- 403 non-owner cannot access a private file's chapter
- 200 non-owner CAN access a public file's chapter
- 404 chapter does not exist
- 409 chapter exists but audio not yet generated
- 404 non-owner DELETE on a public file is denied
"""
from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from unittest.mock import AsyncMock

from api.v1.endpoints.chapters import router as chapters_router
from api.v1.endpoints.files import router as files_router
from core.database import Base, get_db_session
from core.minio import get_minio_client
from core.session import SESSION_COOKIE_NAME, sessions
from models import User, Chapter
from models.file import File, FileStatus, FileVisibility


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def app() -> FastAPI:
    application = FastAPI()
    application.include_router(files_router, prefix="/files")
    application.include_router(chapters_router, prefix="/chapters")
    return application


@pytest.fixture
def session_store() -> Generator:
    sessions.clear()
    yield sessions
    sessions.clear()


@pytest_asyncio.fixture
async def async_session_factory(
    tmp_path,
) -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    db_file = tmp_path / "test.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield session_factory
    await engine.dispose()


@pytest.fixture
def client(
    app: FastAPI,
    async_session_factory: async_sessionmaker[AsyncSession],
) -> Generator[TestClient, None, None]:
    async def _override_db() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = _override_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


async def _create_user(factory: async_sessionmaker[AsyncSession], email: str) -> User:
    async with factory() as session:
        user = User(email=email, hashed_password="hash", is_active=True)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def _create_file(
    factory: async_sessionmaker[AsyncSession],
    user_id: int,
    visibility: FileVisibility = FileVisibility.PRIVATE,
) -> File:
    async with factory() as session:
        f = File(
            user_id=user_id,
            original_filename="book.pdf",
            stored_filename=f"stored_{user_id}.pdf",
            file_size=1024,
            mime_type="application/pdf",
            bucket_name="raw-pdf-uploads",
            status=FileStatus.COMPLETED,
            visibility=visibility,
            upload_date=datetime.now(timezone.utc),
        )
        session.add(f)
        await session.commit()
        await session.refresh(f)
        return f


async def _create_chapter(
    factory: async_sessionmaker[AsyncSession],
    file_id: int,
    *,
    with_audio: bool = True,
) -> Chapter:
    async with factory() as session:
        ch = Chapter(
            file_id=file_id,
            chapter_index=1,
            title="Chapter 1",
            content="Some text.",
            start_page=1,
            end_page=5,
            audio_bucket_name="completed-files" if with_audio else None,
            audio_object_name=f"{file_id}/1.wav" if with_audio else None,
        )
        session.add(ch)
        await session.commit()
        await session.refresh(ch)
        return ch


def _login(client: TestClient, session_store: dict, user: User) -> None:
    token = f"token-{user.id}"
    session_store[token] = {"user_id": user.id, "email": user.email}
    client.cookies.set(SESSION_COOKIE_NAME, token)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_audio_requires_authentication(
    client: TestClient,
) -> None:
    response = client.get("/chapters/1/audio")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_owner_can_get_audio(
    app: FastAPI,
    client: TestClient,
    async_session_factory: async_sessionmaker[AsyncSession],
    session_store: dict,
) -> None:
    owner = await _create_user(async_session_factory, "owner@example.com")
    file_ = await _create_file(async_session_factory, owner.id, FileVisibility.PRIVATE)
    chapter = await _create_chapter(async_session_factory, file_.id)

    _login(client, session_store, owner)

    fake_minio = AsyncMock()
    fake_minio.generate_presigned_url = AsyncMock(return_value="http://minio/signed-url")
    app.dependency_overrides[get_minio_client] = lambda: fake_minio

    response = client.get(f"/chapters/{chapter.id}/audio")

    app.dependency_overrides.pop(get_minio_client, None)

    assert response.status_code == 200
    data = response.json()
    assert data["chapter_id"] == chapter.id
    assert data["url"] == "http://minio/signed-url"
    assert data["expires_in_seconds"] == 3600


@pytest.mark.asyncio
async def test_non_owner_blocked_on_private_file(
    client: TestClient,
    async_session_factory: async_sessionmaker[AsyncSession],
    session_store: dict,
) -> None:
    owner = await _create_user(async_session_factory, "owner2@example.com")
    other = await _create_user(async_session_factory, "other2@example.com")
    file_ = await _create_file(async_session_factory, owner.id, FileVisibility.PRIVATE)
    chapter = await _create_chapter(async_session_factory, file_.id)

    _login(client, session_store, other)

    response = client.get(f"/chapters/{chapter.id}/audio")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_non_owner_allowed_on_public_file(
    app: FastAPI,
    client: TestClient,
    async_session_factory: async_sessionmaker[AsyncSession],
    session_store: dict,
) -> None:
    owner = await _create_user(async_session_factory, "owner3@example.com")
    other = await _create_user(async_session_factory, "other3@example.com")
    file_ = await _create_file(async_session_factory, owner.id, FileVisibility.PUBLIC)
    chapter = await _create_chapter(async_session_factory, file_.id)

    _login(client, session_store, other)

    fake_minio = AsyncMock()
    fake_minio.generate_presigned_url = AsyncMock(return_value="http://minio/public-url")
    app.dependency_overrides[get_minio_client] = lambda: fake_minio

    response = client.get(f"/chapters/{chapter.id}/audio")

    app.dependency_overrides.pop(get_minio_client, None)

    assert response.status_code == 200
    assert response.json()["url"] == "http://minio/public-url"


@pytest.mark.asyncio
async def test_chapter_not_found(
    client: TestClient,
    async_session_factory: async_sessionmaker[AsyncSession],
    session_store: dict,
) -> None:
    user = await _create_user(async_session_factory, "user4@example.com")
    _login(client, session_store, user)

    response = client.get("/chapters/99999/audio")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_audio_not_yet_generated(
    client: TestClient,
    async_session_factory: async_sessionmaker[AsyncSession],
    session_store: dict,
) -> None:
    owner = await _create_user(async_session_factory, "owner5@example.com")
    file_ = await _create_file(async_session_factory, owner.id)
    chapter = await _create_chapter(async_session_factory, file_.id, with_audio=False)

    _login(client, session_store, owner)

    response = client.get(f"/chapters/{chapter.id}/audio")
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_non_owner_cannot_delete_public_file(
    client: TestClient,
    async_session_factory: async_sessionmaker[AsyncSession],
    session_store: dict,
) -> None:
    owner = await _create_user(async_session_factory, "owner6@example.com")
    other = await _create_user(async_session_factory, "other6@example.com")
    file_ = await _create_file(async_session_factory, owner.id, FileVisibility.PUBLIC)

    _login(client, session_store, other)

    response = client.delete(f"/files/{file_.id}")
    assert response.status_code == 404
