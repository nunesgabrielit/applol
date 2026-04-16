from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.config import Settings
from app.services.champion_service import ChampionService
from app.utils.cache import ChampionCache


RAW_AATROX = {
    "version": "15.6.1",
    "id": "Aatrox",
    "key": "266",
    "name": "Aatrox",
    "title": "a Espada Darkin",
    "blurb": "Aatrox é um Darkin.",
    "tags": ["Fighter", "Tank"],
    "partype": "Blood Well",
    "stats": {"hp": 650, "movespeed": 345},
}

RAW_AHRI = {
    "version": "15.6.1",
    "id": "Ahri",
    "key": "103",
    "name": "Ahri",
    "title": "a Raposa de Nove Caudas",
    "blurb": "Ahri é uma maga.",
    "tags": ["Mage", "Assassin"],
    "partype": "Mana",
    "stats": {"hp": 590, "movespeed": 330},
}


class FakeRiotClient:
    def __init__(self, payload: dict, version: str = "15.6.1") -> None:
        self.payload = payload
        self.version = version
        self.fetch_calls = 0

    async def fetch_latest_version(self) -> str:
        return self.version

    async def fetch_champions_payload(self, version: str, locale: str) -> dict:
        self.fetch_calls += 1
        return self.payload


def build_settings() -> Settings:
    return Settings(
        APP_NAME="lol-champions-api",
        APP_ENV="test",
        DEFAULT_DDRAGON_VERSION="15.6.1",
        CACHE_TTL_SECONDS=3600,
        DEFAULT_LOCALE="pt_BR",
        REQUEST_TIMEOUT_SECONDS=5,
    )


def build_service() -> ChampionService:
    payload = {"data": {"Aatrox": RAW_AATROX, "Ahri": RAW_AHRI}}
    return ChampionService(riot_client=FakeRiotClient(payload), settings=build_settings())


@pytest.mark.asyncio
async def test_normalize_champion() -> None:
    service = build_service()
    champion = service.normalize_champion(RAW_AATROX)

    assert champion["key"] == 266
    assert champion["riot_id"] == "Aatrox"
    assert champion["icon_url"].endswith("/266.png")
    assert champion["stats"]["hp"] == 650


@pytest.mark.asyncio
async def test_filter_by_name() -> None:
    service = build_service()
    await service.refresh_cache(force=True)

    result = await service.list_champions(search="ahri")

    assert result["total"] == 1
    assert result["items"][0]["riot_id"] == "Ahri"


@pytest.mark.asyncio
async def test_filter_by_tag() -> None:
    service = build_service()
    await service.refresh_cache(force=True)

    result = await service.list_champions(tag="mage")

    assert result["total"] == 1
    assert result["items"][0]["riot_id"] == "Ahri"


@pytest.mark.asyncio
async def test_get_by_key() -> None:
    service = build_service()
    await service.refresh_cache(force=True)

    champion = await service.get_champion_by_key("266")

    assert champion["riot_id"] == "Aatrox"


@pytest.mark.asyncio
async def test_get_by_name() -> None:
    service = build_service()
    await service.refresh_cache(force=True)

    champion = await service.get_champion_by_name("aatrox")

    assert champion["key"] == 266


@pytest.mark.asyncio
async def test_sort_by_key_desc() -> None:
    service = build_service()
    await service.refresh_cache(force=True)

    result = await service.list_champions(sort_by="key", order="desc")

    assert [item["key"] for item in result["items"]] == [266, 103]


@pytest.mark.asyncio
async def test_refresh_cache_updates_expiration() -> None:
    payload = {"data": {"Aatrox": RAW_AATROX}}
    client = FakeRiotClient(payload)
    service = ChampionService(riot_client=client, settings=build_settings())

    first = await service.refresh_cache(force=True)

    assert first.champions_count == 1
    assert first.expires_at > first.refreshed_at
    assert client.fetch_calls == 1

    service.cache = ChampionCache(
        version=service.cache.version,
        language=service.cache.language,
        last_refresh=datetime.now(UTC) - timedelta(hours=2),
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
        champions=service.cache.champions,
        by_key=service.cache.by_key,
        by_name=service.cache.by_name,
        tags=service.cache.tags,
    )

    second = await service.ensure_cache()

    assert len(second.champions) == 1
    assert client.fetch_calls == 2
