from __future__ import annotations

import asyncio
import logging
import math
import unicodedata
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, status

from app.config import Settings
from app.schemas import CacheMeta
from app.services.riot_client import RiotApiError, RiotClient
from app.utils.cache import ChampionCache


logger = logging.getLogger(__name__)


class ChampionService:
    """Coordinates Riot fetches, normalization, cache refresh, and query operations."""

    def __init__(self, riot_client: RiotClient, settings: Settings) -> None:
        self.riot_client = riot_client
        self.settings = settings
        self.cache = ChampionCache()
        self._refresh_lock = asyncio.Lock()

    async def startup(self) -> None:
        try:
            await self.refresh_cache(force=True)
        except HTTPException as exc:
            logger.warning("Initial champion cache warmup failed: %s", exc.detail)

    async def ensure_cache(self) -> ChampionCache:
        now = datetime.now(UTC)
        if not self.cache.champions or self.cache.is_expired(now):
            await self.refresh_cache(force=not self.cache.champions)
        return self.cache

    async def refresh_cache(self, force: bool = False) -> CacheMeta:
        now = datetime.now(UTC)
        if not force and self.cache.champions and not self.cache.is_expired(now):
            return self._cache_meta(self.cache)

        async with self._refresh_lock:
            now = datetime.now(UTC)
            if not force and self.cache.champions and not self.cache.is_expired(now):
                return self._cache_meta(self.cache)

            version = await self.riot_client.fetch_latest_version()
            language = self.settings.default_locale
            try:
                payload = await self.riot_client.fetch_champions_payload(version=version, locale=language)
            except RiotApiError:
                fallback_locale = self.settings.fallback_locale
                logger.warning("Primary locale '%s' failed, trying fallback locale '%s'.", language, fallback_locale)
                try:
                    payload = await self.riot_client.fetch_champions_payload(version=version, locale=fallback_locale)
                    language = fallback_locale
                except RiotApiError as exc:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Champion data is temporarily unavailable from Riot public endpoints.",
                    ) from exc

            champions = [
                self.normalize_champion(raw_champion)
                for raw_champion in payload.get("data", {}).values()
            ]

            champions.sort(key=lambda item: item["name"].casefold())
            by_key = {str(champion["key"]): champion for champion in champions}
            by_name: dict[str, dict[str, Any]] = {}
            for champion in champions:
                by_name[self.normalize_text(champion["name"])] = champion
                by_name[self.normalize_text(champion["riot_id"])] = champion
                by_name[self.normalize_text(str(champion["key"]))] = champion

            tags = sorted({tag for champion in champions for tag in champion["tags"]}, key=str.casefold)
            expires_at = now + timedelta(seconds=self.settings.cache_ttl_seconds)

            self.cache = ChampionCache(
                version=version,
                language=language,
                last_refresh=now,
                expires_at=expires_at,
                champions=champions,
                by_key=by_key,
                by_name=by_name,
                tags=tags,
            )
            logger.info("Champion cache refreshed with %s champions for version %s.", len(champions), version)
            return self._cache_meta(self.cache)

    def normalize_champion(self, raw_champion: dict[str, Any]) -> dict[str, Any]:
        key_text = str(raw_champion["key"])
        key_value = int(key_text) if key_text.isdigit() else key_text
        return {
            "key": key_value,
            "riot_id": raw_champion["id"],
            "name": raw_champion["name"],
            "title": raw_champion.get("title", ""),
            "blurb": raw_champion.get("blurb"),
            "tags": list(raw_champion.get("tags", [])),
            "partype": raw_champion.get("partype"),
            "stats": dict(raw_champion.get("stats", {})),
            "icon_url": self.settings.community_dragon_icon_template.format(champion_key=key_text),
        }

    def normalize_text(self, value: str) -> str:
        normalized = unicodedata.normalize("NFD", value)
        without_marks = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
        return without_marks.strip().casefold()

    async def get_meta(self) -> dict[str, Any]:
        cache = await self.ensure_cache()
        return {
            "game": "league-of-legends",
            "language": cache.language,
            "ddragon_version": cache.version,
            "champions_count": len(cache.champions),
            "cache_expires_in_seconds": max(
                0,
                math.ceil((cache.expires_at - datetime.now(UTC)).total_seconds()) if cache.expires_at else 0,
            ),
        }

    async def list_champions(
        self,
        search: str | None = None,
        tag: str | None = None,
        limit: int | None = None,
        offset: int = 0,
        sort_by: str = "name",
        order: str = "asc",
    ) -> dict[str, Any]:
        cache = await self.ensure_cache()
        items = cache.champions

        if search:
            search_normalized = self.normalize_text(search)
            items = [
                champion
                for champion in items
                if search_normalized in self.normalize_text(champion["name"])
                or search_normalized in self.normalize_text(champion["riot_id"])
                or search_normalized in self.normalize_text(str(champion["key"]))
            ]

        if tag:
            tag_normalized = self.normalize_text(tag)
            items = [
                champion
                for champion in items
                if any(self.normalize_text(champion_tag) == tag_normalized for champion_tag in champion["tags"])
            ]

        reverse = order.lower() == "desc"
        if sort_by == "key":
            items = sorted(items, key=lambda champion: int(champion["key"]) if str(champion["key"]).isdigit() else champion["key"], reverse=reverse)
        else:
            items = sorted(items, key=lambda champion: champion["name"].casefold(), reverse=reverse)

        total = len(items)
        sliced = items[offset:]
        if limit is not None:
            sliced = sliced[:limit]

        summary_items = [
            {
                "key": champion["key"],
                "riot_id": champion["riot_id"],
                "name": champion["name"],
                "title": champion["title"],
                "tags": champion["tags"],
                "icon_url": champion["icon_url"],
            }
            for champion in sliced
        ]
        return {"total": total, "items": summary_items}

    async def get_champion_by_key(self, champion_key: str) -> dict[str, Any]:
        cache = await self.ensure_cache()
        champion = cache.by_key.get(str(champion_key))
        if not champion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Champion with key '{champion_key}' was not found.",
            )
        return champion

    async def get_champion_by_name(self, name: str) -> dict[str, Any]:
        cache = await self.ensure_cache()
        champion = cache.by_name.get(self.normalize_text(name))
        if not champion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Champion with name or Riot ID '{name}' was not found.",
            )
        return champion

    async def get_tags(self) -> list[str]:
        cache = await self.ensure_cache()
        return cache.tags

    def _cache_meta(self, cache: ChampionCache) -> CacheMeta:
        return CacheMeta(
            language=cache.language or self.settings.default_locale,
            ddragon_version=cache.version or self.settings.default_ddragon_version,
            champions_count=len(cache.champions),
            refreshed_at=cache.last_refresh or datetime.now(UTC),
            expires_at=cache.expires_at or datetime.now(UTC),
        )
