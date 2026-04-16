from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="lol-champions-api", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    default_ddragon_version: str = Field(default="15.6.1", alias="DEFAULT_DDRAGON_VERSION")
    cache_ttl_seconds: int = Field(default=43_200, alias="CACHE_TTL_SECONDS")
    default_locale: str = Field(default="pt_BR", alias="DEFAULT_LOCALE")
    request_timeout_seconds: float = Field(default=20.0, alias="REQUEST_TIMEOUT_SECONDS")

    versions_url: str = "https://ddragon.leagueoflegends.com/api/versions.json"
    ddragon_url_template: str = "https://ddragon.leagueoflegends.com/cdn/{version}/data/{locale}/champion.json"
    community_dragon_icon_template: str = (
        "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/"
        "champion-icons/{champion_key}.png"
    )

    @property
    def fallback_locale(self) -> str:
        return "en_US" if self.default_locale.lower() != "en_us" else "pt_BR"


@lru_cache
def get_settings() -> Settings:
    return Settings()
