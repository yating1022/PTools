from fastapi import APIRouter, Body, Form, HTTPException, Query

from app.database import SessionLocal
from app.dependencies import GyFileDep
from app.models.gy import GyConfig

router = APIRouter(prefix="/gy/files", tags=["gy-files"])


def _safe(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("")
async def list_files(
    file_svc: GyFileDep,
    parent_id: str = Query(default="", description="父文件夹 ID，空表示根目录"),
    type: str | None = Query(default=None, description="文件类型过滤: image/video/document"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
):
    return _safe(file_svc.list_files, parent_id, type, page, page_size)


@router.get("/{file_id}")
async def get_file(file_id: str, file_svc: GyFileDep):
    return _safe(file_svc.get_file, file_id)


@router.post("/download")
async def get_download_url(
    file_svc: GyFileDep,
    file_id: str = Query(..., description="文件 ID"),
):
    url = _safe(file_svc.get_download_url, file_id)
    return {"download_url": url}


@router.post("/cloud-download")
async def cloud_download(
    file_svc: GyFileDep,
    url: str = Form(..., description="下载链接"),
    parent_id: str = Form(default="", description="目标文件夹 ID"),
):
    return _safe(file_svc.cloud_download, url, parent_id)


@router.get("/cloud-tasks")
async def list_cloud_tasks(
    file_svc: GyFileDep,
    status: list[int] | None = Query(default=None, description="状态过滤: 1=等待 2=下载中 3=完成 5=失败"),
    page_size: int = Query(default=50, ge=1, le=100),
):
    return _safe(file_svc.list_cloud_tasks, status, page_size)


@router.post("/cloud-tasks/{task_id}/retry")
async def retry_cloud_task(task_id: str, file_svc: GyFileDep):
    return _safe(file_svc.retry_cloud_task, task_id)


@router.delete("/cloud-tasks")
async def delete_cloud_task(
    file_svc: GyFileDep,
    task_ids: list[str] = Body(..., description="任务 ID 列表"),
):
    return _safe(file_svc.delete_cloud_task, task_ids)


@router.post("/cloud-download-batch")
async def cloud_download_batch(
    file_svc: GyFileDep,
    urls: str = Form(..., description="多个下载链接，每行一个"),
    parent_id: str = Form(default="", description="目标文件夹 ID"),
):
    lines = [u.strip() for u in urls.replace("\r\n", "\n").split("\n") if u.strip()]
    if not lines:
        raise HTTPException(status_code=400, detail="没有有效的下载链接")

    results = []
    for url in lines:
        try:
            _safe(file_svc.cloud_download, url, parent_id)
            results.append({"url": url, "status": "ok"})
        except Exception as e:
            detail = str(e)
            # HTTPException 的 detail 在 .detail 里
            if hasattr(e, "detail"):
                detail = e.detail
            results.append({"url": url, "status": "error", "detail": detail})

    ok = sum(1 for r in results if r["status"] == "ok")
    return {"results": results, "total": len(results), "ok": ok, "fail": len(results) - ok}


@router.get("/config/cloud-folder")
async def get_cloud_folder():
    with SessionLocal() as db:
        cfg = db.query(GyConfig).filter(GyConfig.key == "cloud_download_folder").first()
        return {"folder_id": cfg.value if cfg else ""}


@router.put("/config/cloud-folder")
async def set_cloud_folder(
    folder_id: str = Form(..., description="默认云下载文件夹 ID，空字符串表示根目录"),
):
    with SessionLocal() as db:
        cfg = db.query(GyConfig).filter(GyConfig.key == "cloud_download_folder").first()
        if cfg:
            cfg.value = folder_id
        else:
            db.add(GyConfig(key="cloud_download_folder", value=folder_id))
        db.commit()
    return {"folder_id": folder_id}
