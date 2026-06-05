from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Query, UploadFile

from app.services.gy_magnet_service import GyMagnetService, get_gy_magnet_service

router = APIRouter(prefix="/gy/magnets", tags=["gy-magnets"])

MagnetDep = Annotated[GyMagnetService, Depends(get_gy_magnet_service)]


@router.post("/import")
async def import_magnets(
    svc: MagnetDep,
    file: UploadFile,
):
    if not file.filename or not file.filename.endswith((".xlsx", ".xls", ".csv", ".tsv")):
        raise HTTPException(status_code=400, detail="请上传 .xlsx / .xls / .csv 文件")
    data = await file.read()
    try:
        result = svc.import_excel(data)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"解析失败: {e}")


@router.get("")
async def list_magnets(
    svc: MagnetDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    keyword: str | None = Query(default=None),
):
    return svc.list_magnets(page, page_size, keyword)


@router.get("/{bangou}")
async def get_magnet(bangou: str, svc: MagnetDep):
    result = svc.get_magnet(bangou)
    if not result:
        raise HTTPException(status_code=404, detail="未找到")
    return result


@router.delete("")
async def delete_magnets(
    svc: MagnetDep,
    ids: list[int] = Body(..., embed=True),
):
    count = svc.delete_magnets(ids)
    return {"deleted": count}
