#!/usr/bin/env python3
"""
Generate a complete League of Legends champion dataset with:
- counters (5)
- against (5)
- synergy_good (3)
- synergy_bad (3)

Important
---------
This script does NOT use real matchup/synergy win-rate data.
It uses deterministic heuristics based on Data Dragon tags/roles
to produce a stable dataset for seeding and experimentation.

Usage:
    python scripts/generate_lol_dataset.py

Outputs:
- lol_full_dataset.json
- lol_full_dataset.csv
"""

from __future__ import annotations

import asyncio
import csv
import json
import logging
import os
import random
from dataclasses import dataclass
from typing import Any

import httpx

VERSIONS_URL = "https://ddragon.leagueoflegends.com/api/versions.json"
CHAMPIONS_URL = "https://ddragon.leagueoflegends.com/cdn/{version}/data/{locale}/champion.json"

DEFAULT_LOCALE = os.getenv("LOL_LOCALE", "pt_BR")
FALLBACK_LOCALE = os.getenv("LOL_FALLBACK_LOCALE", "en_US")
DEFAULT_VERSION = os.getenv("LOL_DEFAULT_VERSION", "16.6.1")
REQUEST_TIMEOUT = float(os.getenv("LOL_REQUEST_TIMEOUT", "20"))
JSON_OUTPUT = os.getenv("LOL_JSON_OUTPUT", "lol_full_dataset.json")
CSV_OUTPUT = os.getenv("LOL_CSV_OUTPUT", "lol_full_dataset.csv")
RANDOM_SEED = int(os.getenv("LOL_RANDOM_SEED", "42"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("lol-dataset-generator")


@dataclass(slots=True)
class Champion:
    key: int
    riot_id: str
    name: str
    title: str
    tags: list[str]
    primary_role: str


class DatasetGenerationError(Exception):
    """Raised when dataset generation fails."""


def normalize_role(tags: list[str]) -> str:
    if not tags:
        return "Unknown"
    preferred_order = ["Fighter", "Tank", "Mage", "Assassin", "Marksman", "Support"]
    for role in preferred_order:
        if role in tags:
            return role
    return tags[0]


def unique_preserve(items: list[str], exclude: str | None = None) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if exclude and item == exclude:
            continue
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def role_counter_map() -> dict[str, list[str]]:
    return {
        "Assassin": ["Mage", "Marksman"],
        "Tank": ["Assassin"],
        "Marksman": ["Tank"],
        "Mage": ["Fighter"],
        "Fighter": ["Tank"],
        "Support": ["Mage", "Marksman"],
        "Unknown": ["Mage", "Marksman"],
    }


def role_against_map() -> dict[str, list[str]]:
    return {
        "Assassin": ["Tank"],
        "Tank": ["Fighter", "Marksman"],
        "Marksman": ["Assassin"],
        "Mage": ["Assassin"],
        "Fighter": ["Mage"],
        "Support": ["Assassin", "Mage"],
        "Unknown": ["Assassin", "Tank"],
    }


def role_synergy_good_map() -> dict[str, list[str]]:
    return {
        "Assassin": ["Tank", "Support", "Mage"],
        "Tank": ["Marksman", "Mage", "Support"],
        "Marksman": ["Tank", "Support", "Mage"],
        "Mage": ["Tank", "Support", "Marksman"],
        "Fighter": ["Support", "Mage", "Tank"],
        "Support": ["Marksman", "Mage", "Tank"],
        "Unknown": ["Tank", "Support", "Mage"],
    }


def role_synergy_bad_map() -> dict[str, list[str]]:
    return {
        "Assassin": ["Assassin", "Marksman"],
        "Tank": ["Tank"],
        "Marksman": ["Marksman", "Assassin"],
        "Mage": ["Mage", "Assassin"],
        "Fighter": ["Fighter", "Assassin"],
        "Support": ["Support"],
        "Unknown": ["Unknown", "Assassin"],
    }


async def fetch_json(client: httpx.AsyncClient, url: str) -> Any:
    response = await client.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


async def get_latest_version(client: httpx.AsyncClient) -> str:
    try:
        versions = await fetch_json(client, VERSIONS_URL)
        if isinstance(versions, list) and versions:
            logger.info("Latest version found: %s", versions[0])
            return str(versions[0])
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to fetch versions.json; using fallback %s. Reason: %s", DEFAULT_VERSION, exc)
    return DEFAULT_VERSION


async def get_champion_payload(client: httpx.AsyncClient, version: str, locale: str) -> dict[str, Any]:
    url = CHAMPIONS_URL.format(version=version, locale=locale)
    payload = await fetch_json(client, url)
    if not isinstance(payload, dict) or "data" not in payload:
        raise DatasetGenerationError(f"Unexpected champion payload for locale {locale}")
    return payload


async def get_champions(client: httpx.AsyncClient) -> tuple[str, str, list[Champion]]:
    version = await get_latest_version(client)

    payload: dict[str, Any] | None = None
    chosen_locale = DEFAULT_LOCALE

    try:
        payload = await get_champion_payload(client, version, DEFAULT_LOCALE)
        chosen_locale = DEFAULT_LOCALE
        logger.info("Loaded champion.json using locale %s", DEFAULT_LOCALE)
    except Exception as exc_primary:  # noqa: BLE001
        logger.warning("Primary locale %s failed: %s", DEFAULT_LOCALE, exc_primary)
        try:
            payload = await get_champion_payload(client, version, FALLBACK_LOCALE)
            chosen_locale = FALLBACK_LOCALE
            logger.info("Loaded champion.json using fallback locale %s", FALLBACK_LOCALE)
        except Exception as exc_fallback:  # noqa: BLE001
            raise DatasetGenerationError(
                f"Could not load champion.json in either {DEFAULT_LOCALE} or {FALLBACK_LOCALE}: {exc_fallback}"
            ) from exc_fallback

    raw_data = payload["data"]
    champions: list[Champion] = []

    for riot_id, raw in raw_data.items():
        try:
            key = int(raw["key"])
            name = str(raw["name"])
            title = str(raw.get("title", ""))
            tags = [str(tag) for tag in raw.get("tags", [])]
            primary_role = normalize_role(tags)
            champions.append(
                Champion(
                    key=key,
                    riot_id=str(riot_id),
                    name=name,
                    title=title,
                    tags=tags,
                    primary_role=primary_role,
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Champion skipped due to parse error: %s | error=%s", raw, exc)

    champions.sort(key=lambda champion: champion.name.lower())
    if not champions:
        raise DatasetGenerationError("No champions were loaded from Data Dragon.")

    logger.info("Total champions loaded: %s", len(champions))
    return version, chosen_locale, champions


def grouped_by_role(champions: list[Champion]) -> dict[str, list[Champion]]:
    grouped: dict[str, list[Champion]] = {}
    for champion in champions:
        grouped.setdefault(champion.primary_role, []).append(champion)
    for members in grouped.values():
        members.sort(key=lambda champion: champion.name.lower())
    return grouped


def stable_shuffle(names: list[str], seed_value: int) -> list[str]:
    rng = random.Random(seed_value)
    copied = names[:]
    rng.shuffle(copied)
    return copied


def pick_from_roles(
    champion: Champion,
    grouped: dict[str, list[Champion]],
    target_roles: list[str],
    min_count: int,
    all_champions: list[Champion],
    seed_offset: int,
) -> list[str]:
    pool: list[str] = []

    for role in target_roles:
        for candidate in grouped.get(role, []):
            if candidate.name != champion.name:
                pool.append(candidate.name)

    pool = stable_shuffle(unique_preserve(pool, exclude=champion.name), champion.key + seed_offset)

    if len(pool) < min_count:
        fallback_pool = [
            candidate.name
            for candidate in all_champions
            if candidate.name != champion.name and candidate.name not in pool
        ]
        fallback_pool = stable_shuffle(fallback_pool, champion.key + seed_offset + 999)
        pool.extend(fallback_pool)

    return unique_preserve(pool, exclude=champion.name)[:min_count]


def build_dataset(champions: list[Champion], version: str, locale: str) -> dict[str, Any]:
    grouped = grouped_by_role(champions)
    counter_rules = role_counter_map()
    against_rules = role_against_map()
    synergy_good_rules = role_synergy_good_map()
    synergy_bad_rules = role_synergy_bad_map()

    items: list[dict[str, Any]] = []

    for champion in champions:
        counters = pick_from_roles(
            champion=champion,
            grouped=grouped,
            target_roles=counter_rules.get(champion.primary_role, ["Mage", "Marksman"]),
            min_count=5,
            all_champions=champions,
            seed_offset=10,
        )
        against = pick_from_roles(
            champion=champion,
            grouped=grouped,
            target_roles=against_rules.get(champion.primary_role, ["Assassin", "Tank"]),
            min_count=5,
            all_champions=champions,
            seed_offset=20,
        )
        synergy_good = pick_from_roles(
            champion=champion,
            grouped=grouped,
            target_roles=synergy_good_rules.get(champion.primary_role, ["Tank", "Support", "Mage"]),
            min_count=3,
            all_champions=champions,
            seed_offset=30,
        )
        synergy_bad = pick_from_roles(
            champion=champion,
            grouped=grouped,
            target_roles=synergy_bad_rules.get(champion.primary_role, ["Assassin"]),
            min_count=3,
            all_champions=champions,
            seed_offset=40,
        )

        items.append(
            {
                "key": champion.key,
                "riot_id": champion.riot_id,
                "name": champion.name,
                "title": champion.title,
                "primary_role": champion.primary_role,
                "tags": champion.tags,
                "counters": counters,
                "against": against,
                "synergy_good": synergy_good,
                "synergy_bad": synergy_bad,
            }
        )

    return {
        "meta": {
            "game": "League of Legends",
            "generator": "heuristic-role-based",
            "note": (
                "This dataset is generated heuristically from Data Dragon tags. "
                "It does not represent real win rate, tier lists, or official matchup/synergy statistics."
            ),
            "version": version,
            "locale": locale,
            "champions_count": len(items),
            "seed": RANDOM_SEED,
        },
        "champions": items,
    }


def export_json(data: dict[str, Any], filepath: str) -> None:
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
    logger.info("JSON generated at %s", filepath)


def export_csv(data: dict[str, Any], filepath: str) -> None:
    fieldnames = [
        "key",
        "riot_id",
        "name",
        "title",
        "primary_role",
        "tags",
        "counters",
        "against",
        "synergy_good",
        "synergy_bad",
    ]

    with open(filepath, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for item in data["champions"]:
            writer.writerow(
                {
                    "key": item["key"],
                    "riot_id": item["riot_id"],
                    "name": item["name"],
                    "title": item["title"],
                    "primary_role": item["primary_role"],
                    "tags": "|".join(item["tags"]),
                    "counters": "|".join(item["counters"]),
                    "against": "|".join(item["against"]),
                    "synergy_good": "|".join(item["synergy_good"]),
                    "synergy_bad": "|".join(item["synergy_bad"]),
                }
            )

    logger.info("CSV generated at %s", filepath)


async def async_main() -> None:
    random.seed(RANDOM_SEED)
    async with httpx.AsyncClient(follow_redirects=True) as client:
        version, locale, champions = await get_champions(client)
        dataset = build_dataset(champions, version=version, locale=locale)
        export_json(dataset, JSON_OUTPUT)
        export_csv(dataset, CSV_OUTPUT)
        logger.info("Done: %s champions processed.", dataset["meta"]["champions_count"])


def main() -> None:
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        logger.error("Execution interrupted by user.")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Dataset generation failed: %s", exc)


if __name__ == "__main__":
    main()
