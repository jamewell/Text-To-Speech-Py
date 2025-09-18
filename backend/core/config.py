import os
from typing import List
from pydantic import field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    PROJECT_NAME: str = os.getenv("PROJECT_NAME")
    VERSION: str = os.getenv("VERSION")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT")
    DEBUG: bool = os.getenv("DEBUG")

    HOST: str = os.getenv("HOST")
    PORT: int = os.getenv("PORT")
    API_V1_STR: str = os.getenv("API_V1_STR")

    ALLOWED_HOSTS: List[str] = ["http://localhost:5173"]

    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST")
    POSTGRES_PORT: int = os.getenv("POSTGRES_PORT")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB")

    REDIS_HOST: str = os.getenv("REDIS_HOST")
    REDIS_PORT: int = os.getenv("REDIS_PORT")
    REDIS_DB: int = os.getenv("REDIS_DB")
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD")

    MINIO_HOST: str = os.getenv("MINIO_HOST")
    MINIO_PORT: int = os.getenv("MINIO_PORT")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY")
    MINIO_BUCKET_NAME: str = os.getenv("MINIO_BUCKET_NAME")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE")

    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND")

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="forbid"
    )

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError("ALLOWED_HOSTS must be a list or comma-separated string")

    @staticmethod
    def _build_redis_url(data: dict) -> str:
        redis_host = data.get("REDIS_HOST", "localhost")
        redis_port = data.get("REDIS_PORT", 6379)
        redis_db = data.get("REDIS_DB", 0)
        redis_password = data.get("REDIS_PASSWORD", "")

        auth = f":{redis_password}@" if redis_password else ""
        return f"redis://{auth}{redis_host}:{redis_port}/{redis_db}"

    @field_validator("CELERY_BROKER_URL", mode="before")
    @classmethod
    def assemble_celery_broker_url(cls, v, info):

        if v:
            return v

        data = info.data if info.data else {}
        return cls._build_redis_url(data)

    @field_validator("CELERY_RESULT_BACKEND", mode="before")
    @classmethod
    def assemble_celery_result_backend(cls, v, info):
        if v:
            return v

        data = info.data if info.data else {}
        return cls._build_redis_url(data)

    @computed_field
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.REDIS_DB}"
        )

    @computed_field
    @property
    def redis_url(self) -> str:
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


settings = Settings()