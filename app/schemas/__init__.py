from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str = "ok"


class ChampionSummary(BaseModel):
    key: int
    riot_id: str
    name: str
    title: str
    tags: list[str]
    icon_url: str


class ChampionDetail(ChampionSummary):
    blurb: str | None = None
    partype: str | None = None
    stats: dict[str, Any] = Field(default_factory=dict)


class ChampionRankStat(BaseModel):
    label: str
    slug: str
    win_rate: float | None = None
    popularity: float | None = None


class ChampionRoleStat(BaseModel):
    label: str
    slug: str
    win_rate: float | None = None
    pick_rate: float | None = None


class ChampionPerformanceResponse(BaseModel):
    source: str
    source_url: str
    summary: str
    caveat: str
    tier: str | None = None
    role_stats: list[ChampionRoleStat]
    strong_against: list[str]
    weak_against: list[str]


class ChampionsListResponse(BaseModel):
    total: int
    items: list[ChampionSummary]


class MetaResponse(BaseModel):
    game: str = "league-of-legends"
    language: str
    ddragon_version: str
    champions_count: int
    cache_expires_in_seconds: int


class TagsResponse(BaseModel):
    items: list[str]


class RefreshResponse(BaseModel):
    status: str = "refreshed"
    language: str
    ddragon_version: str
    champions_count: int
    refreshed_at: datetime
    expires_at: datetime


class CacheMeta(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    language: str
    ddragon_version: str
    champions_count: int
    refreshed_at: datetime
    expires_at: datetime


class CounterPickEntry(BaseModel):
    enemy_champion: str
    ideal_adc: str
    ideal_support: str
    reason: str


class CounterGuideResponse(BaseModel):
    total: int
    items: list[CounterPickEntry]


class EnemyTeamRequest(BaseModel):
    top: str | None = None
    jungler: str | None = None
    mid: str | None = None
    carry: str | None = None
    sup: str | None = None


class RecommendationChoice(BaseModel):
    champion: str
    votes: int


class MatchedCounter(BaseModel):
    role: str
    enemy_champion: str
    ideal_adc: str
    ideal_support: str
    reason: str


class RecommendationResponse(BaseModel):
    suggested_adc: RecommendationChoice | None = None
    suggested_support: RecommendationChoice | None = None
    adc_ranking: list[RecommendationChoice]
    support_ranking: list[RecommendationChoice]
    matched_counters: list[MatchedCounter]
    missing_roles: list[str]
    unknown_entries: list[str]


class AnalyticsListItem(BaseModel):
    label: str
    count: int
    share: float


class AnalyticsDuoItem(BaseModel):
    adc: str
    support: str
    count: int
    share: float


class AnalyticsOverviewResponse(BaseModel):
    total_entries: int
    unique_enemy_champions: int
    unique_adc_recommendations: int
    unique_support_recommendations: int
    strongest_duo: AnalyticsDuoItem | None = None
    most_present_champions: list[AnalyticsListItem]
    top_enemy_appearance: list[AnalyticsListItem]
    top_adc_recommendations: list[AnalyticsListItem]
    top_support_recommendations: list[AnalyticsListItem]
    strongest_combinations: list[AnalyticsDuoItem]
    enemy_appearance_is_uniform: bool = False
    dataset_meta: dict[str, str | None] = Field(default_factory=dict)


class ChampionDatasetResponse(BaseModel):
    class ChampionDeckSynergy(BaseModel):
        champion: str
        reason: str | None = None

    class ChampionDeckProfile(BaseModel):
        label: str
        counters: list[str]
        against: list[str]
        synergy_label: str
        synergies: list["ChampionDatasetResponse.ChampionDeckSynergy"]
        warning: str | None = None

    key: int
    riot_id: str
    name: str
    title: str
    primary_role: str
    tags: list[str]
    counters: list[str]
    against: list[str]
    synergy_good: list[str]
    synergy_bad: list[str]
    note: str | None = None
    profiles: list["ChampionDatasetResponse.ChampionDeckProfile"] = Field(default_factory=list)
