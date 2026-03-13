"""Unit tests for CoquiTTSService."""
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from services.tts import CoquiTTSService


@pytest.mark.asyncio
async def test_synthesize_returns_audio_bytes() -> None:
    fake_audio = b"RIFF\x24\x00\x00\x00WAVEfmt "

    mock_response = MagicMock()
    mock_response.content = fake_audio
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("services.tts.httpx.AsyncClient", return_value=mock_client):
        result = await CoquiTTSService.synthesize("Hello world")

    assert result == fake_audio
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    assert call_args.kwargs.get("json", {}).get("text") == "Hello world"


@pytest.mark.asyncio
async def test_synthesize_raises_on_http_error() -> None:
    mock_request = MagicMock()
    mock_resp = MagicMock()
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError("500", request=mock_request, response=mock_resp)
    )

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("services.tts.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(httpx.HTTPStatusError):
            await CoquiTTSService.synthesize("Hello world")


@pytest.mark.asyncio
async def test_synthesize_raises_on_connection_error() -> None:
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=httpx.ConnectError("connection refused"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("services.tts.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(httpx.ConnectError):
            await CoquiTTSService.synthesize("Hello world")
