from functools import lru_cache
from pathlib import Path

from app.config import Settings, get_settings
from app.services.dataset_service import DatasetService
from app.services.champion_service import ChampionService
from app.services.counter_service import CounterService
from app.services.lolalytics_service import LolalyticsService
from app.services.riot_client import RiotClient


@lru_cache
def get_champion_service() -> ChampionService:
    settings: Settings = get_settings()
    riot_client = RiotClient(settings=settings)
    return ChampionService(riot_client=riot_client, settings=settings)


@lru_cache
def get_counter_service() -> CounterService:
    data_path = Path(__file__).resolve().parent.parent / "data" / "counter_picks.json"
    return CounterService(data_path=data_path)


@lru_cache
def get_dataset_service() -> DatasetService:
    data_path = Path(__file__).resolve().parent.parent / "data" / "lol_full_dataset.json"
    profiles_path = Path(__file__).resolve().parent.parent / "data" / "champion_deck_profiles.json"
    return DatasetService(data_path=data_path, profiles_path=profiles_path)


@lru_cache
def get_lolalytics_service() -> LolalyticsService:
    settings: Settings = get_settings()
    return LolalyticsService(settings=settings)
