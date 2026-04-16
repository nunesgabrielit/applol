from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_champion_service, get_lolalytics_service
from app.schemas import ChampionDetail, ChampionPerformanceResponse, ChampionsListResponse
from app.services.champion_service import ChampionService
from app.services.lolalytics_service import LolalyticsService


router = APIRouter(tags=["champions"])


@router.get("/champions", response_model=ChampionsListResponse)
async def list_champions(
    search: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    limit: int | None = Query(default=None, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    sort_by: Literal["name", "key"] = Query(default="name"),
    order: Literal["asc", "desc"] = Query(default="asc"),
    service: ChampionService = Depends(get_champion_service),
) -> ChampionsListResponse:
    payload = await service.list_champions(
        search=search,
        tag=tag,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        order=order,
    )
    return ChampionsListResponse(**payload)


@router.get("/champions/{champion_key}", response_model=ChampionDetail)
async def get_champion(champion_key: str, service: ChampionService = Depends(get_champion_service)) -> ChampionDetail:
    return ChampionDetail(**(await service.get_champion_by_key(champion_key)))


@router.get("/champions/by-name/{name}", response_model=ChampionDetail)
async def get_champion_by_name(name: str, service: ChampionService = Depends(get_champion_service)) -> ChampionDetail:
    return ChampionDetail(**(await service.get_champion_by_name(name)))


@router.get("/champions/{champion_key}/performance", response_model=ChampionPerformanceResponse)
async def get_champion_performance(
    champion_key: str,
    champion_service: ChampionService = Depends(get_champion_service),
    performance_service: LolalyticsService = Depends(get_lolalytics_service),
) -> ChampionPerformanceResponse:
    champion = await champion_service.get_champion_by_key(champion_key)
    payload = await performance_service.get_champion_snapshot(str(champion["riot_id"]))
    return ChampionPerformanceResponse(**payload)
