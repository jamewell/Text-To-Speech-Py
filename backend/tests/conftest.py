from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.v1.endpoints.files import router as files_router
from core.database import Base, get_db_session
from core.session import sessions


@pytest.fixture
def app() -> FastAPI:
    application = FastAPI()
    application.include_router(files_router, prefix="/files")
    return application


@pytest.fixture
def session_store() -> Generator:
    sessions.clear()
    yield sessions
    sessions.clear()


@pytest_asyncio.fixture
async def async_session_factory(
    tmp_path
) -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    db_file = tmp_path / "test.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield session_factory
    await engine.dispose()


@pytest.fixture
def client(
    app: FastAPI,
    async_session_factory: async_sessionmaker[AsyncSession],
) -> Generator[TestClient, None, None]:
    async def _override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = _override_get_db_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
