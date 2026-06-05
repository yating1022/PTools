import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import router
from app.config import settings

logging.basicConfig(
    level=logging.DEBUG if settings.app.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.database import engine, init_db
    import app.models  # noqa: F401 — 注册所有 ORM 模型
    init_db()

    # 给 gy_magnets 表加新列（已有表 create_all 不会加列）
    from sqlalchemy import text
    with engine.begin() as conn:
        for ddl in [
            "ALTER TABLE gy_magnets ADD COLUMN downloaded TINYINT(1) NOT NULL DEFAULT 0",
            "ALTER TABLE gy_magnets ADD COLUMN downloaded_at DATETIME NULL",
        ]:
            try:
                conn.execute(text(ddl))
            except Exception:
                pass  # 列已存在则忽略

    # 启动每日入库调度器
    from app.services.gy_daily_import_service import get_gy_daily_import_service
    svc = get_gy_daily_import_service()
    svc.start_scheduler()

    logger.info("Application starting on %s:%s", settings.app.host, settings.app.port)
    yield
    svc.stop_scheduler()
    logger.info("Application shutting down")


app = FastAPI(
    title=settings.app.title,
    version=settings.app.version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


app.include_router(router)


# ── Serve frontend static files (Docker) ─────────────────
from pathlib import Path

_static_dir = Path(__file__).parent.parent / "static"
if _static_dir.is_dir():
    from fastapi.staticfiles import StaticFiles
    from starlette.responses import FileResponse

    app.mount("/assets", StaticFiles(directory=str(_static_dir / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path == "health":
            return {"status": "healthy"}
        file = _static_dir / full_path
        if file.is_file():
            return FileResponse(str(file))
        return FileResponse(str(_static_dir / "index.html"))
else:
    @app.get("/health")
    async def health():
        return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
    )
