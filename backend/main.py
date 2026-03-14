import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.config import settings
from core.logging_config import setup_logging
from api.v1.api import api_router

setup_logging()

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(application: FastAPI):
    logger.info(
        "Application startup initiated",
        extra={
            "project_name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG
        }
    )

    logger.info("Checking database connection...")
    try:
        from core.database import check_database_connection, create_tables, run_schema_migrations

        connection_ok = await check_database_connection()
        if not connection_ok:
            logger.error("Database connection failed - exiting")
            raise Exception("Database connection failed")

        logger.info("🗄️ Initializing database tables...")
        await create_tables()
        await run_schema_migrations()

    except Exception as e:
        logger.error(
            "Database initialization failed",
            extra={"error": str(e)},
            exc_info=True
        )
        logger.info("Make sure PostgreSQL is running and credentials are correct")
        raise

    logger.info("Application startup complete")

    yield

    logger.info("🛑 Shutting down application...")


def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        description="FastAPI backend for TTS web application with async processing",
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    application.include_router(api_router, prefix=settings.API_V1_STR)

    logger.info(
        "FastAPI application created",
        extra={
            "allowed_hosts": settings.ALLOWED_HOSTS,
            "api_prefix": settings.API_V1_STR
        }
    )

    return application


app = create_application()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )