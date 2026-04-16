from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class ChampionCache:
    """In-memory cache snapshot for champion data."""

    version: str | None = None
    language: str | None = None
    last_refresh: datetime | None = None
    expires_at: datetime | None = None
    champions: list[dict] = field(default_factory=list)
    by_key: dict[str, dict] = field(default_factory=dict)
    by_name: dict[str, dict] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)

    def is_expired(self, now: datetime) -> bool:
        return self.expires_at is None or now >= self.expires_at
