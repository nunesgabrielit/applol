from fastapi import APIRouter, Depends

from app.dependencies import get_champion_service
from app.schemas import MetaResponse, RefreshResponse, TagsResponse
from app.services.champion_service import ChampionService


router = APIRouter(tags=["meta"])


@router.get("/meta", response_model=MetaResponse)
async def get_meta(service: ChampionService = Depends(get_champion_service)) -> MetaResponse:
    return MetaResponse(**(await service.get_meta()))


@router.get("/tags", response_model=TagsResponse)
async def get_tags(service: ChampionService = Depends(get_champion_service)) -> TagsResponse:
    return TagsResponse(items=await service.get_tags())


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(service: ChampionService = Depends(get_champion_service)) -> RefreshResponse:
    meta = await service.refresh_cache(force=True)
    return RefreshResponse(
        language=meta.language,
        ddragon_version=meta.ddragon_version,
        champions_count=meta.champions_count,
        refreshed_at=meta.refreshed_at,
        expires_at=meta.expires_at,
    )
