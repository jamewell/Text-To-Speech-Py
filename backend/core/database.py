from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from .config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.database_url,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_recycle=300,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    try:

        import models

        print(f"🗄️ Found {len(Base.metadata.tables)} tables to create:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Database tables created successfully")

    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        raise


async def drop_tables():
    try:
        import models

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            print("✅ Database tables dropped successfully")

    except Exception as e:
        print(f"❌ Error dropping database tables: {e}")
        raise


async def check_database_connection():
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.fetchone()
            print("✅ Database connection successful")
            return True

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False