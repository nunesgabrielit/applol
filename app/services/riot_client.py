from __future__ import annotations

import logging

import httpx

from app.config import Settings


logger = logging.getLogger(__name__)


class RiotApiError(RuntimeError):
    """Raised when Riot public endpoints are unavailable or malformed."""


class RiotClient:
    """Small async client for Riot public champion metadata endpoints."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def fetch_latest_version(self) -> str:
        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.get(self.settings.versions_url)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Could not fetch Data Dragon versions, falling back to default version: %s", exc)
            return self.settings.default_ddragon_version

        payload = response.json()
        if isinstance(payload, list) and payload:
            return str(payload[0])

        logger.warning("Versions endpoint returned unexpected payload, using default version.")
        return self.settings.default_ddragon_version

    async def fetch_champions_payload(self, version: str, locale: str) -> dict:
        url = self.settings.ddragon_url_template.format(version=version, locale=locale)
        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.get(url)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RiotApiError(f"Failed to fetch champion data for locale '{locale}'.") from exc

        payload = response.json()
        if not isinstance(payload, dict) or "data" not in payload:
            raise RiotApiError("Champion payload from Data Dragon is malformed.")

        return payload
