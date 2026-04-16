from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_counter_service, get_dataset_service
from app.schemas import AnalyticsOverviewResponse, ChampionDatasetResponse, CounterGuideResponse, EnemyTeamRequest, RecommendationResponse
from app.services.counter_service import CounterService
from app.services.dataset_service import DatasetService


router = APIRouter(tags=["counters"])


@router.get("/counters", response_model=CounterGuideResponse)
async def list_counter_guide(service: CounterService = Depends(get_counter_service)) -> CounterGuideResponse:
    return CounterGuideResponse(**service.list_items())


@router.get("/analytics/overview", response_model=AnalyticsOverviewResponse)
async def get_analytics_overview(service: DatasetService = Depends(get_dataset_service)) -> AnalyticsOverviewResponse:
    payload = service.get_analytics()
    return AnalyticsOverviewResponse(**payload)


@router.get("/analytics/champions/{champion_key}", response_model=ChampionDatasetResponse)
async def get_analytics_champion(
    champion_key: str,
    service: DatasetService = Depends(get_dataset_service),
) -> ChampionDatasetResponse:
    champion = service.get_champion_entry(champion_key)
    if not champion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Champion '{champion_key}' was not found in the generated dataset.",
        )
    return ChampionDatasetResponse(**champion)


@router.post("/counters/recommend", response_model=RecommendationResponse)
async def recommend_picks(
    payload: EnemyTeamRequest,
    service: CounterService = Depends(get_counter_service),
) -> RecommendationResponse:
    return RecommendationResponse(**service.recommend(payload.model_dump()))
