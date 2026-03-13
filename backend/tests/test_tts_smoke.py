"""
Smoke tests for the Coqui TTS HTTP contract.

Uses an in-process mock server so the tests always run and verify that:
  - CoquiTTSService.synthesize() sends POST with a JSON body
  - Non-empty text returns audio bytes
  - Empty text raises HTTPStatusError (server rejects it with 400)

This approach catches regressions in tts.py without requiring a live
Coqui instance and without relying on test-time connectivity checks.
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from types import SimpleNamespace

import httpx
import pytest

from services.tts import CoquiTTSService

_FAKE_WAV = b"RIFF\x00\x00\x00\x00WAVEfmt "


class _TtsHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path != "/api/tts":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))
        text = body.get("text", "")

        if not text:
            self.send_response(400)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Length", str(len(_FAKE_WAV)))
        self.end_headers()
        self.wfile.write(_FAKE_WAV)

    def log_message(self, format: str, *args: object) -> None:
        pass  # suppress request logs during tests


@pytest.fixture(scope="module")
def mock_tts_url() -> str:
    server = HTTPServer(("127.0.0.1", 0), _TtsHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


@pytest.mark.asyncio
async def test_synthesize_returns_audio_for_valid_text(
    mock_tts_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("services.tts.settings", SimpleNamespace(TTS_SERVICE_URL=mock_tts_url))
    audio = await CoquiTTSService.synthesize("Hello world")
    assert audio == _FAKE_WAV


@pytest.mark.asyncio
async def test_synthesize_raises_for_empty_text(
    mock_tts_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("services.tts.settings", SimpleNamespace(TTS_SERVICE_URL=mock_tts_url))
    with pytest.raises(httpx.HTTPStatusError):
        await CoquiTTSService.synthesize("")
