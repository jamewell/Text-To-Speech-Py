"""
Structural validation of docker-compose.yml for the coqui-tts service.

These tests parse the compose file and assert the properties that caused
previous runtime failures (wrong entrypoint, missing healthcheck, etc.).
They are skipped automatically when the infra directory is not accessible,
e.g. when pytest runs inside the backend container without the infra mount.
"""
from __future__ import annotations

import pathlib

import pytest
import yaml

_here = pathlib.Path(__file__).resolve()
COMPOSE_FILE = next(
    (p / "infra" / "docker-compose.yml" for p in _here.parents
     if (p / "infra" / "docker-compose.yml").exists()),
    None,
)

skip_if_no_compose = pytest.mark.skipif(
    COMPOSE_FILE is None,
    reason="infra/docker-compose.yml not accessible from this environment",
)


@pytest.fixture(scope="module")
def compose() -> dict:
    with COMPOSE_FILE.open() as f:  # type: ignore[union-attr]
        return yaml.safe_load(f)


@skip_if_no_compose
def test_coqui_service_present(compose: dict) -> None:
    assert "coqui-tts" in compose["services"], "coqui-tts service must be defined"


@skip_if_no_compose
def test_coqui_entrypoint_overrides_image_default(compose: dict) -> None:
    """Image default entrypoint is 'tts' CLI; must be overridden to 'tts-server'."""
    coqui = compose["services"]["coqui-tts"]
    assert "entrypoint" in coqui, (
        "coqui-tts must set entrypoint explicitly — "
        "the image default ('tts') will reject tts-server arguments"
    )
    entrypoint = coqui["entrypoint"]
    flat = " ".join(entrypoint) if isinstance(entrypoint, list) else entrypoint
    assert "tts-server" in flat, f"entrypoint must invoke tts-server, got: {flat!r}"


@skip_if_no_compose
def test_coqui_command_contains_model_and_port(compose: dict) -> None:
    coqui = compose["services"]["coqui-tts"]
    cmd = coqui.get("command", [])
    flat = " ".join(cmd) if isinstance(cmd, list) else cmd
    assert "--model_name" in flat
    assert "--port" in flat


@skip_if_no_compose
def test_coqui_has_healthcheck(compose: dict) -> None:
    coqui = compose["services"]["coqui-tts"]
    assert "healthcheck" in coqui, "coqui-tts must define a healthcheck"
    assert coqui["healthcheck"].get("start_period"), "healthcheck must have start_period for model load time"


@skip_if_no_compose
def test_celery_waits_for_coqui_healthy(compose: dict) -> None:
    depends = compose["services"]["celery"].get("depends_on", {})
    assert "coqui-tts" in depends, "celery must depend on coqui-tts"
    assert depends["coqui-tts"].get("condition") == "service_healthy", (
        "celery must use condition: service_healthy for coqui-tts "
        "so tasks are not dispatched before the model is loaded"
    )
