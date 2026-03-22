"""
Tests for POST /history/{file_id} and GET /history/ endpoints.

Covers:
- 401 when unauthenticated (POST and GET)
- POST creates a new history record
- POST upserts — second call updates position, same DB row
- POST on non-existent file → 404
- POST on private file owned by other user → 404 (no information leak)
- POST on public file owned by other user → 200
- GET returns only the calling user's records
- GET with no history returns empty list
- position_seconds < 0 → 422
- chapter_id is optional (omit from body) → chapter_id null in response
- GET pagination
"""
from __future__ import annotations

import itertools
from collections.abc import AsyncGenerator, Generator
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.v1.endpoints.files import router as files_router
from api.v1.endpoints.history import router as history_router
from core.database import Base, get_db_session
from core.session import SESSION_COOKIE_NAME, sessions
from models import User, Chapter
from models.file import File, FileStatus, FileVisibility
from models.reading_history import ReadingHistory

_file_counter = itertools.count(1)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def app() -> FastAPI:
    application = FastAPI()
    application.include_router(files_router, prefix="/files")
    application.include_router(history_router, prefix="/history")
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
            stored_filename=f"stored_{next(_file_counter)}.pdf",
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
) -> Chapter:
    async with factory() as session:
        ch = Chapter(
            file_id=file_id,
            chapter_index=1,
            title="Chapter 1",
            content="Some text.",
            start_page=1,
            end_page=5,
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
async def test_post_history_requires_authentication(client: TestClient) -> None:
    response = client.post("/history/1", json={"position_seconds": 10.0})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_history_requires_authentication(client: TestClient) -> None:
    response = client.get("/history/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_post_creates_new_history_record(
    client: TestClient,
    async_session_factory: async_sessionmaker[AsyncSession],
    session_store: dict,
) -> None:
    user = await _create_user(async_session_factory, "user1@example.com")
    file_ = await _create_file(async_session_factory, user.id)
    _login(client, session_store, user)

    response = client.post(f"/history/{file_.id}", json={"position_seconds": 42.5})

    assert response.status_code == 200
    data = response.json()
    assert data["file_id"] == file_.id
    assert data["user_id"] == user.id
    assert data["position_seconds"] == 42.5
    assert data["chapter_id"] is None

    # Verify record exists in DB
    async with async_session_factory() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(ReadingHistory).where(
                ReadingHistory.user_id == user.id,
                ReadingHistory.file_id == file_.id,
            )
        )
        record = result.scalar_one_or_none()
    assert record is not None
    assert record.position_seconds == 42.5


@pytest.mark.asyncio
async def test_post_upserts_existing_record(
    client: TestClient,
    async_session_factory: async_sessionmaker[AsyncSession],
    session_store: dict,
) -> None:
    user = await _create_user(async_session_factory, "user2@example.com")
    file_ = await _create_file(async_session_factory, user.id)
    _login(client, session_store, user)

    r1 = client.post(f"/history/{file_.id}", json={"position_seconds": 10.0})
    assert r1.status_code == 200
    first_id = r1.json()["id"]

    r2 = client.post(f"/history/{file_.id}", json={"position_seconds": 99.9})
    assert r2.status_code == 200
    data = r2.json()

    # Same row updated
    assert data["id"] == first_id
    assert data["position_seconds"] == 99.9

    # Only one record in DB
    async with async_session_factory() as session:
        from sqlalchemy import select, func
        count_result = await session.execute(
            select(func.count()).select_from(ReadingHistory).where(
                ReadingHistory.user_id == user.id,
                ReadingHistory.file_id == file_.id,
            )
        )
        assert count_result.scalar_one() == 1


@pytest.mark.asyncio
async def test_post_non_existent_file_returns_404(
    client: TestClient,
    async_session_factory: async_sessionmaker[AsyncSession],
    session_store: dict,
) -> None:
    user = await _create_user(async_session_factory, "user3@example.com")
    _login(client, session_store, user)

    response = client.post("/history/99999", json={"position_seconds": 5.0})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_post_private_file_other_user_returns_404(
    client: TestClient,
    async_session_factory: async_sessionmaker[AsyncSession],
    session_store: dict,
) -> None:
    owner = await _create_user(async_session_factory, "owner4@example.com")
    other = await _create_user(async_session_factory, "other4@example.com")
    file_ = await _create_file(async_session_factory, owner.id, FileVisibility.PRIVATE)

    _login(client, session_store, other)

    response = client.post(f"/history/{file_.id}", json={"position_seconds": 5.0})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_post_public_file_other_user_returns_200(
    client: TestClient,
    async_session_factory: async_sessionmaker[AsyncSession],
    session_store: dict,
) -> None:
    owner = await _create_user(async_session_factory, "owner5@example.com")
    other = await _create_user(async_session_factory, "other5@example.com")
    file_ = await _create_file(async_session_factory, owner.id, FileVisibility.PUBLIC)

    _login(client, session_store, other)

    response = client.post(f"/history/{file_.id}", json={"position_seconds": 15.0})
    assert response.status_code == 200
    assert response.json()["user_id"] == other.id


@pytest.mark.asyncio
async def test_get_returns_only_calling_users_records(
    client: TestClient,
    async_session_factory: async_sessionmaker[AsyncSession],
    session_store: dict,
) -> None:
    user_a = await _create_user(async_session_factory, "usera@example.com")
    user_b = await _create_user(async_session_factory, "userb@example.com")
    file_a = await _create_file(async_session_factory, user_a.id)
    file_b = await _create_file(async_session_factory, user_b.id, FileVisibility.PUBLIC)

    # user_a posts progress on their own file
    _login(client, session_store, user_a)
    client.post(f"/history/{file_a.id}", json={"position_seconds": 30.0})

    # user_b posts progress on their own file
    _login(client, session_store, user_b)
    client.post(f"/history/{file_b.id}", json={"position_seconds": 60.0})

    # user_a's GET should only return their own record
    _login(client, session_store, user_a)
    response = client.get("/history/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert all(r["user_id"] == user_a.id for r in data["history"])


@pytest.mark.asyncio
async def test_get_empty_history(
    client: TestClient,
    async_session_factory: async_sessionmaker[AsyncSession],
    session_store: dict,
) -> None:
    user = await _create_user(async_session_factory, "user6@example.com")
    _login(client, session_store, user)

    response = client.get("/history/")
    assert response.status_code == 200
    data = response.json()
    assert data["history"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_negative_position_seconds_returns_422(
    client: TestClient,
    async_session_factory: async_sessionmaker[AsyncSession],
    session_store: dict,
) -> None:
    user = await _create_user(async_session_factory, "user7@example.com")
    file_ = await _create_file(async_session_factory, user.id)
    _login(client, session_store, user)

    response = client.post(f"/history/{file_.id}", json={"position_seconds": -1.0})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chapter_id_is_optional(
    client: TestClient,
    async_session_factory: async_sessionmaker[AsyncSession],
    session_store: dict,
) -> None:
    user = await _create_user(async_session_factory, "user8@example.com")
    file_ = await _create_file(async_session_factory, user.id)
    chapter = await _create_chapter(async_session_factory, file_.id)
    _login(client, session_store, user)

    # With chapter_id
    r1 = client.post(f"/history/{file_.id}", json={"position_seconds": 5.0, "chapter_id": chapter.id})
    assert r1.status_code == 200
    assert r1.json()["chapter_id"] == chapter.id

    # Without chapter_id — should clear it
    r2 = client.post(f"/history/{file_.id}", json={"position_seconds": 5.0})
    assert r2.status_code == 200
    assert r2.json()["chapter_id"] is None


@pytest.mark.asyncio
async def test_get_pagination(
    client: TestClient,
    async_session_factory: async_sessionmaker[AsyncSession],
    session_store: dict,
) -> None:
    user = await _create_user(async_session_factory, "user9@example.com")
    _login(client, session_store, user)

    # Create 3 history records across 3 different files
    for i in range(3):
        file_ = await _create_file(async_session_factory, user.id)
        client.post(f"/history/{file_.id}", json={"position_seconds": float(i * 10)})

    # Page 1, size 2 → 2 results
    r1 = client.get("/history/?page=1&page_size=2")
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["total"] == 3
    assert len(d1["history"]) == 2
    assert d1["page"] == 1
    assert d1["page_size"] == 2

    # Page 2, size 2 → 1 result
    r2 = client.get("/history/?page=2&page_size=2")
    assert r2.status_code == 200
    d2 = r2.json()
    assert len(d2["history"]) == 1


@pytest.mark.asyncio
async def test_post_nonexistent_chapter_id_returns_422(
    client: TestClient,
    async_session_factory: async_sessionmaker[AsyncSession],
    session_store: dict,
) -> None:
    user = await _create_user(async_session_factory, "user10@example.com")
    file_ = await _create_file(async_session_factory, user.id)
    _login(client, session_store, user)

    response = client.post(f"/history/{file_.id}", json={"position_seconds": 5.0, "chapter_id": 99999})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_cross_file_chapter_id_returns_422(
    client: TestClient,
    async_session_factory: async_sessionmaker[AsyncSession],
    session_store: dict,
) -> None:
    user = await _create_user(async_session_factory, "user11@example.com")
    file_a = await _create_file(async_session_factory, user.id)
    file_b = await _create_file(async_session_factory, user.id)
    chapter_b = await _create_chapter(async_session_factory, file_b.id)
    _login(client, session_store, user)

    # chapter_b belongs to file_b but we're posting to file_a's history
    response = client.post(
        f"/history/{file_a.id}",
        json={"position_seconds": 5.0, "chapter_id": chapter_b.id},
    )
    assert response.status_code == 422
