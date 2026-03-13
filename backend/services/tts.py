"""Coqui TTS service for text-to-speech conversion via HTTP."""
from __future__ import annotations

import logging

import httpx

from core.config import settings

logger = logging.getLogger(__name__)


class CoquiTTSService:
    """Calls the Coqui TTS HTTP server and returns raw audio bytes."""

    @staticmethod
    async def synthesize(text: str) -> bytes:
        """
        Convert text to speech using the Coqui TTS service.

        Args:
            text: Text to synthesize.

        Returns:
            WAV audio bytes.

        Raises:
            httpx.HTTPStatusError: If the TTS service returns a non-2xx response.
            httpx.RequestError: If the TTS service is unreachable.
        """
        url = f"{settings.TTS_SERVICE_URL}/api/tts"

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json={"text": text})
            response.raise_for_status()

        logger.info(
            "TTS synthesis completed",
            extra={"text_length": len(text), "audio_bytes": len(response.content)},
        )

        return response.content
