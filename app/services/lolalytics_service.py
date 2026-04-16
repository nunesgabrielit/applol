from __future__ import annotations

import asyncio
import logging
import re
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from html import unescape
from typing import Any

import httpx

from app.config import Settings


logger = logging.getLogger(__name__)

ROLE_LABELS = {
    "top": "Top",
    "jungle": "Jungle",
    "middle": "Mid",
    "bottom": "ADC",
    "support": "Support",
}


@dataclass
class CachedLolalyticsPayload:
    expires_at: datetime
    payload: dict[str, Any]


class LolalyticsService:
    """Fetches lightweight public champion snapshots from LoLalytics."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = "https://lolalytics.com/pt_br/lol"
        self.cache_ttl = timedelta(hours=6)
        self._cache: dict[str, CachedLolalyticsPayload] = {}
        self._lock = asyncio.Lock()

    async def get_champion_snapshot(self, riot_id: str) -> dict[str, Any]:
        slug = self._slugify(riot_id)
        now = datetime.now(UTC)
        cached = self._cache.get(slug)
        if cached and cached.expires_at > now:
            return cached.payload

        async with self._lock:
            cached = self._cache.get(slug)
            now = datetime.now(UTC)
            if cached and cached.expires_at > now:
                return cached.payload

            payload = await self._fetch_snapshot(slug)
            self._cache[slug] = CachedLolalyticsPayload(
                expires_at=now + self.cache_ttl,
                payload=payload,
            )
            return payload

    async def _fetch_snapshot(self, slug: str) -> dict[str, Any]:
        async with httpx.AsyncClient(
            timeout=self.settings.request_timeout_seconds,
            headers={"User-Agent": "Mozilla/5.0"},
            follow_redirects=True,
        ) as client:
            base_url = f"{self.base_url}/{slug}/build/"
            base_html = await self._fetch_html(client, base_url)

            role_distribution = self._extract_role_distribution(base_html)
            role_tasks = [
                self._fetch_role_stat(client, slug, role_slug)
                for role_slug, pick_rate in role_distribution
                if pick_rate >= 0.5
            ]
            role_stats = await asyncio.gather(*role_tasks)

        role_stats = [item for item in role_stats if item]
        role_stats.sort(key=lambda item: (-(item["pick_rate"] or 0.0), -(item["win_rate"] or 0.0)))

        summary = self._extract_summary(base_html)
        strong_against = self._extract_link_names_after_marker(summary, "strong counter to", 3)
        weak_against = self._extract_link_names_after_marker(summary, "countered most by", 3)
        cleaned_summary = self._clean_html(summary)
        tier = self._extract_tier(cleaned_summary)

        if role_stats:
            top_role = role_stats[0]
            summary_text = (
                f"Melhor leitura rapida: {top_role['label']} com {self._fmt(top_role['win_rate'])} de win rate "
                f"e {self._fmt(top_role['pick_rate'])} de pick rate."
            )
        else:
            summary_text = "Snapshot publico do LoLalytics indisponivel no momento."

        return {
            "source": "LoLalytics",
            "source_url": base_url,
            "summary": summary_text,
            "caveat": (
                "Referencia publica do LoLalytics em pt_BR. Valores resumidos de rotas e counters podem variar por patch e tier."
            ),
            "tier": tier,
            "role_stats": role_stats,
            "strong_against": strong_against,
            "weak_against": weak_against,
        }

    async def _fetch_role_stat(
        self,
        client: httpx.AsyncClient,
        slug: str,
        role_slug: str,
    ) -> dict[str, Any] | None:
        url = f"{self.base_url}/{slug}/build/?lane={role_slug}"
        html = await self._fetch_html(client, url)
        if not html:
            return None

        summary = self._extract_summary(html)
        clean_summary = self._clean_html(summary)
        match = re.search(r"has a ([0-9]+(?:\.[0-9]+)?)% win rate in ([A-Za-z+]+)", clean_summary)
        if not match:
            return None

        pick_rate = dict(self._extract_role_distribution(html)).get(role_slug)
        return {
          "label": ROLE_LABELS.get(role_slug, role_slug.title()),
          "slug": role_slug,
          "win_rate": float(match.group(1)),
          "pick_rate": pick_rate,
        }

    async def _fetch_html(self, client: httpx.AsyncClient, url: str) -> str:
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as exc:
            logger.warning("LoLalytics request failed for %s: %s", url, exc)
            return ""

    def _extract_summary(self, html: str) -> str:
        match = re.search(r'<p class="lolx-links[^"]*".*?>(.*?)</p>', html, re.S)
        return match.group(1) if match else ""

    def _extract_role_distribution(self, html: str) -> list[tuple[str, float]]:
        matches = re.findall(
            r'/build/\?lane=(top|jungle|middle|bottom|support)".*?text-\[9px\].*?>([0-9]+(?:\.[0-9]+)?)%',
            html,
            re.S,
        )
        seen: dict[str, float] = {}
        for role_slug, value in matches:
            seen.setdefault(role_slug, float(value))
        return list(seen.items())

    def _extract_link_names_after_marker(self, html_fragment: str, marker: str, limit: int) -> list[str]:
        idx = html_fragment.find(marker)
        if idx == -1:
            return []
        tail = html_fragment[idx:]
        names = re.findall(r">([^<]+)</a>", tail)
        cleaned = []
        for name in names:
            value = self._clean_html(name)
            if value and value not in cleaned:
                cleaned.append(value)
            if len(cleaned) == limit:
                break
        return cleaned

    def _extract_tier(self, summary: str) -> str | None:
        match = re.search(r"in ([A-Za-z+]+) on Patch", summary)
        return match.group(1) if match else None

    def _clean_html(self, value: str) -> str:
        without_tags = re.sub(r"<[^>]+>", "", value)
        collapsed = re.sub(r"\s+", " ", unescape(without_tags)).strip()
        return collapsed

    def _slugify(self, value: str) -> str:
        normalized = unicodedata.normalize("NFD", value)
        without_marks = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
        return re.sub(r"[^a-z0-9]", "", without_marks.casefold())

    def _fmt(self, value: float | None) -> str:
        return f"{value:.1f}%" if isinstance(value, float) else "-"
