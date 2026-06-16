import logging
from contextlib import asynccontextmanager
from pathlib import Path

import jwt
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

_static_dir = Path(__file__).parent.parent / "static"


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

    # ── 静态文件服务（Docker 环境）── 在所有 API 路由之后注册
    if _static_dir.is_dir():
        from fastapi.staticfiles import StaticFiles
        from starlette.responses import FileResponse

        app.mount("/assets", StaticFiles(directory=str(_static_dir / "assets")), name="assets")

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            file = _static_dir / full_path
            if file.is_file():
                return FileResponse(str(file))
            return FileResponse(str(_static_dir / "index.html"))

        @app.get("/")
        async def serve_root():
            return FileResponse(str(_static_dir / "index.html"))

        logger.info("Serving frontend from %s", _static_dir)
    else:
        @app.get("/health")
        async def health():
            return {"status": "healthy"}

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


@app.middleware("http")
async def auth_gate_middleware(request: Request, call_next):
    path = request.url.path
    if (
        not path.startswith("/api")
        or path == "/api/v1/verify"
    ):
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


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
    )
