from fastapi import APIRouter, Query

from app.schemas import SettingsOut, SettingsUpdate
from app.services.settings import (
    get_settings_out,
    health_check,
    providers_out,
    remote_models,
    save_settings,
)

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsOut)
async def read_settings():
    return get_settings_out()


@router.put("", response_model=SettingsOut)
async def update_settings(payload: SettingsUpdate):
    return save_settings(payload)


@router.get("/providers")
async def settings_providers():
    return providers_out()


@router.get("/health")
async def settings_health(
    provider: str | None = Query(None),
    model: str | None = Query(None),
):
    return await health_check(provider, model)


@router.get("/remote-models")
async def settings_remote_models(
    provider: str | None = Query(None),
    base_url: str | None = Query(None),
    key: str | None = Query(None),
):
    return await remote_models(provider, base_url=base_url, api_key=key)
