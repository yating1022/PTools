import logging
from contextlib import asynccontextmanager
from pathlib import Path

import jwt
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import router
from app.config import settings

logging.basicConfig(
    level=logging.DEBUG if settings.app.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

_static_dir = Path(__file__).parent.parent / "static"
_is_docker = _static_dir.is_dir()


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.database import engine, init_db
    import app.models  # noqa: F401 — 注册所有 ORM 模型
    init_db()

    from sqlalchemy import text
    with engine.begin() as conn:
        for ddl in [
            "ALTER TABLE gy_magnets ADD COLUMN downloaded TINYINT(1) NOT NULL DEFAULT 0",
            "ALTER TABLE gy_magnets ADD COLUMN downloaded_at DATETIME NULL",
        ]:
            try:
                conn.execute(text(ddl))
            except Exception:
                pass

    from app.services.gy_daily_import_service import get_gy_daily_import_service
    svc = get_gy_daily_import_service()
    svc.start_scheduler()

    logger.info("Application starting on %s:%s (docker=%s)", settings.app.host, settings.app.port, _is_docker)
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


# ── Auth middleware ──────────────────────────────────────
@app.middleware("http")
async def auth_gate_middleware(request: Request, call_next):
    path = request.url.path
    if not path.startswith("/api") or path == "/api/v1/verify":
        return await call_next(request)

    auth = request.headers.get("authorization", "")
    token = auth.removeprefix("Bearer ").strip() if auth.startswith("Bearer ") else ""
    if not token:
        return JSONResponse(status_code=401, content={"detail": "未验证，请先输入访问密钥"})

    try:
        jwt.decode(token, settings.app.secret_key, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return JSONResponse(status_code=401, content={"detail": "密钥已过期，请重新验证"})
    except jwt.InvalidTokenError:
        return JSONResponse(status_code=401, content={"detail": "无效密钥"})

    return await call_next(request)


# ── API 路由 ────────────────────────────────────────────
app.include_router(router)


# ── Health（独立于 catch-all）────────────────────────────
@app.get("/health")
async def health():
    return {"status": "healthy"}


# ── 静态文件 + SPA fallback（Docker 环境）───────────────
if _is_docker:
    from fastapi.staticfiles import StaticFiles

    app.mount("/assets", StaticFiles(directory=str(_static_dir / "assets")), name="assets")

    @app.exception_handler(404)
    async def spa_fallback(request: Request, exc: StarletteHTTPException):
        """非 API 请求 404 时返回 index.html（SPA 路由由前端处理）"""
        path = request.url.path
        if path.startswith("/api"):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})

        file = _static_dir / path.lstrip("/")
        if file.is_file():
            return FileResponse(str(file))
        return FileResponse(str(_static_dir / "index.html"))


# ── 通用异常处理 ────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error: %s", exc, exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
    )
