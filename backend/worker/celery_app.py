"""
Celery application configuration and initialization.
Handles task queue setup for async TTS processing.
"""
from celery import Celery
from celery.signals import worker_ready, worker_shutdown

from core.config import settings


def create_celery_app() -> Celery:
    """
    Create and configure Celery application.

    Returns:
        Configured Celery instance
    """
    celery_application = Celery(
        "tts-worker",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
        include=["worker.tasks"]
    )

    celery_application.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,

        result_expires=3600,
        result_backend_transport_options={
            "master_name": "mymaster",
            "visibility_timeout": 3600,
        },

        # Task routing and execution
        task_track_started=True,
        task_time_limit=300,  # 5 minutes hard limit
        task_soft_time_limit=240,  # 4 minutes soft limit

        # Performance
        task_acks_late = True,  # Acknowledge tasks after completion
        task_reject_on_worker_lost = True,

        # Task naming
        task_default_queue="tts_default",
        task_routes={
            "worker.tasks.process_tts": {"queue": "tts_processing"},
            "worker.tasks.process_pdf": {"queue": "pdf_processing"},
        },

        # Rate limiting
        task_default_rate_limit="10/m",  # 10 tasks per minute

        # Retry policy defaults
        task_autoretry_for=(Exception,),
        task_retry_kwargs={"max_retries": 3},
        task_retry_backoff=True,
        task_retry_backoff_max=600,  # Max 10 minutes
        task_retry_jitter=True,
    )

    return celery_application

# Create global Celery instance
celery_app = create_celery_app()


def on_worker_ready(sender, **kwargs):
    """Handler called when Celery worker is ready to accept tasks."""
    print("🎯 Celery worker is ready and listening for tasks...")
    print(f"📊 Environment: {settings.ENVIRONMENT}")
    print(f"🔗 Broker: {settings.CELERY_BROKER_URL.split('@')[-1]}")  # Hide password
    print(f"💾 Backend: {settings.CELERY_RESULT_BACKEND.split('@')[-1]}")


def on_worker_shutdown(sender, **kwargs):
    """Handler called when Celery worker is shutting down."""
    print("🛑 Celery worker shutting down...")

# Connect signal handlers
worker_ready.connect(on_worker_ready)
worker_shutdown.connect(on_worker_shutdown)

