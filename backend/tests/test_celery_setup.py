from pathlib import Path
from types import SimpleNamespace
import re

import pytest

from worker.celery_app import create_celery_app


def test_create_celery_app_uses_redis_broker_and_expected_routes(monkeypatch) -> None:
    fake_settings = SimpleNamespace(
        CELERY_BROKER_URL="redis://redis:6379/0",
        CELERY_RESULT_BACKEND="redis://redis:6379/0",
    )
    monkeypatch.setattr("worker.celery_app.settings", fake_settings)

    celery_app = create_celery_app()

    assert celery_app.main == "tts-worker"
    assert celery_app.conf.broker_url == "redis://redis:6379/0"
    assert celery_app.conf.result_backend == "redis://redis:6379/0"
    assert celery_app.conf.task_default_queue == "tts_default"
    assert celery_app.conf.task_routes["worker.tasks.process_pdf"]["queue"] == "pdf_processing"
    assert celery_app.conf.task_routes["worker.tasks.process_tts"]["queue"] == "tts_processing"


def test_docker_compose_configures_celery_worker_and_redis_broker() -> None:
    compose_path = None
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "infra" / "docker-compose.yml"
        if candidate.exists():
            compose_path = candidate
            break

    if compose_path is None:
        pytest.skip("infra/docker-compose.yml not available in this test runtime")

    compose_content = compose_path.read_text(encoding="utf-8")

    assert "  redis:\n" in compose_content
    assert "image: redis:7" in compose_content

    celery_block_match = re.search(
        r"(?ms)^  celery:\n(?P<block>(?:    .*\n)+)",
        compose_content,
    )
    assert celery_block_match is not None

    celery_block = celery_block_match.group("block")
    assert "command: [\"celery\", \"-A\", \"worker.celery_app:celery_app\", \"worker\", \"--loglevel=info\"]" in celery_block
    assert "depends_on:" in celery_block
    assert "- redis" in celery_block
