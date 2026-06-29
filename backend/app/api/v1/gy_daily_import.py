from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.gy_daily_import_service import get_gy_daily_import_service

router = APIRouter(prefix="/gy/daily-import", tags=["gy-daily-import"])


class DailyImportConfig(BaseModel):
    hour: int = Field(default=3, ge=0, le=23)
    count: int = Field(default=10, ge=1)
    enabled: bool = True
    folder: str = ""


@router.get("/config")
async def get_config():
    svc = get_gy_daily_import_service()
    return svc.get_config()


@router.put("/config")
async def save_config(body: DailyImportConfig):
    svc = get_gy_daily_import_service()
    svc.save_config(body.hour, body.count, body.enabled, body.folder)
    return svc.get_config()


@router.get("/status")
async def get_status():
    svc = get_gy_daily_import_service()
    return svc.get_status()


@router.post("/run")
async def trigger_run():
    svc = get_gy_daily_import_service()
    result = svc.run_import()
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
