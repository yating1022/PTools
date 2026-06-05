from fastapi import APIRouter

from app.api.v1 import gy_auth, gy_daily_import, gy_files, gy_magnets

router = APIRouter(prefix="/api/v1")
router.include_router(gy_auth.router)
router.include_router(gy_files.router)
router.include_router(gy_magnets.router)
router.include_router(gy_daily_import.router)
