from app.config import Settings
from app.services.lolalytics_service import LolalyticsService


def build_service() -> LolalyticsService:
    settings = Settings(
        APP_NAME="lol-champions-api",
        APP_ENV="test",
        DEFAULT_DDRAGON_VERSION="15.6.1",
        CACHE_TTL_SECONDS=3600,
        DEFAULT_LOCALE="pt_BR",
        REQUEST_TIMEOUT_SECONDS=5,
    )
    return LolalyticsService(settings=settings)


def test_slugify_special_champions() -> None:
    service = build_service()

    assert service._slugify("Bel'Veth") == "belveth"
    assert service._slugify("Dr. Mundo") == "drmundo"
    assert service._slugify("Kai'Sa") == "kaisa"


def test_extract_role_distribution() -> None:
    service = build_service()
    html = """
    <a href="/pt_br/lol/aatrox/build/?lane=top"><div class="mt-[8px] text-center text-[9px]">85.3%</div></a>
    <a href="/pt_br/lol/aatrox/build/?lane=middle"><div class="mt-[8px] text-center text-[9px]">12.3%</div></a>
    <a href="/pt_br/lol/aatrox/build/?lane=support"><div class="mt-[8px] text-center text-[9px]">0.6%</div></a>
    """

    assert service._extract_role_distribution(html) == [
        ("top", 85.3),
        ("middle", 12.3),
        ("support", 0.6),
    ]
