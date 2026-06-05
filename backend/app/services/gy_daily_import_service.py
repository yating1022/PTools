import logging
import threading
from datetime import datetime, date
from typing import Any

from app.database import SessionLocal
from app.models.gy import GyConfig, GyMagnet

logger = logging.getLogger(__name__)

# 配置 key
_CFG_HOUR = "daily_import_hour"
_CFG_COUNT = "daily_import_count"
_CFG_ENABLED = "daily_import_enabled"


def _read_cfg(db) -> dict[str, Any]:
    rows = db.query(GyConfig).filter(
        GyConfig.key.in_([_CFG_HOUR, _CFG_COUNT, _CFG_ENABLED])
    ).all()
    cfg = {r.key: r.value for r in rows}
    return {
        "hour": int(cfg.get(_CFG_HOUR, "3")),
        "count": int(cfg.get(_CFG_COUNT, "10")),
        "enabled": cfg.get(_CFG_ENABLED, "1") == "1",
    }


def _read_cloud_folder(db) -> str:
    row = db.query(GyConfig).filter(GyConfig.key == "cloud_download_folder").first()
    return row.value if row else ""


def _save_cfg(db, hour: int, count: int, enabled: bool):
    for key, value in [
        (_CFG_HOUR, str(hour)),
        (_CFG_COUNT, str(count)),
        (_CFG_ENABLED, "1" if enabled else "0"),
    ]:
        row = db.query(GyConfig).filter(GyConfig.key == key).first()
        if row:
            row.value = value
        else:
            db.add(GyConfig(key=key, value=value))
    db.commit()


class GyDailyImportService:
    """每日入库服务：定时从磁力表取未下载的磁力进行云下载"""

    def __init__(self):
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._last_run_date: date | None = None
        self._last_run_results: list[dict] = []
        self._last_run_time: str = ""
        self._running = False

    # ── Config ─────────────────────────────────────────────

    def get_config(self) -> dict[str, Any]:
        with SessionLocal() as db:
            cfg = _read_cfg(db)
        return cfg

    def save_config(self, hour: int, count: int, enabled: bool = True):
        hour = max(0, min(23, hour))
        count = max(1, count)
        with SessionLocal() as db:
            _save_cfg(db, hour, count, enabled)
        logger.info("每日入库配置已更新: hour=%d, count=%d, enabled=%s", hour, count, enabled)

    # ── Status ─────────────────────────────────────────────

    def get_status(self) -> dict[str, Any]:
        cfg = self.get_config()
        total_undownloaded = 0
        total_downloaded = 0
        with SessionLocal() as db:
            total_undownloaded = db.query(GyMagnet).filter(GyMagnet.downloaded == False).count()
            total_downloaded = db.query(GyMagnet).filter(GyMagnet.downloaded == True).count()

        next_run = ""
        if cfg["enabled"]:
            now = datetime.now()
            h = cfg["hour"]
            if now.hour < h or (now.hour == h and now.minute == 0 and self._last_run_date == now.date()):
                next_run = f"今天 {h:02d}:00"
            else:
                next_run = f"明天 {h:02d}:00"

        return {
            "enabled": cfg["enabled"],
            "hour": cfg["hour"],
            "count": cfg["count"],
            "is_running": self._running,
            "last_run_time": self._last_run_time,
            "last_run_results": self._last_run_results,
            "next_run": next_run,
            "total_undownloaded": total_undownloaded,
            "total_downloaded": total_downloaded,
        }

    # ── Execute import ─────────────────────────────────────

    def run_import(self) -> dict[str, Any]:
        """执行一次云下载导入"""
        if self._running:
            return {"error": "导入任务正在执行中"}

        self._running = True
        try:
            return self._do_import()
        finally:
            self._running = False

    def _do_import(self) -> dict[str, Any]:
        with SessionLocal() as db:
            cfg = _read_cfg(db)
            folder = _read_cloud_folder(db)
            magnets = (
                db.query(GyMagnet)
                .filter(GyMagnet.downloaded == False)
                .order_by(GyMagnet.id.asc())
                .limit(cfg["count"])
                .all()
            )
            # 提前复制数据，避免 detached instance
            magnet_list = [(m.id, m.bangou, m.magnet) for m in magnets]

        if not magnet_list:
            self._last_run_results = []
            self._last_run_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._last_run_date = date.today()
            return {"results": [], "message": "没有待下载的磁力链接"}

        from app.services.gy_auth_service import get_gy_auth_service
        auth = get_gy_auth_service()
        if not auth.is_authenticated:
            return {"error": "未登录，请先登录光鸭网盘"}

        results = []
        success_ids = []
        client = auth.get_client()
        try:
            for mid, bangou, magnet_url in magnet_list:
                try:
                    client.create_cloud_task(magnet_url, folder)
                    success_ids.append(mid)
                    results.append({"bangou": bangou, "status": "ok"})
                    logger.info("每日入库成功: %s", bangou)
                except Exception as e:
                    results.append({"bangou": bangou, "status": "error", "detail": str(e)})
                    logger.warning("每日入库失败: %s — %s", bangou, e)
        finally:
            client.close()

        # 批量标记已下载
        if success_ids:
            now = datetime.now()
            with SessionLocal() as db:
                db.query(GyMagnet).filter(GyMagnet.id.in_(success_ids)).update(
                    {GyMagnet.downloaded: True, GyMagnet.downloaded_at: now},
                    synchronize_session=False,
                )
                db.commit()

        self._last_run_results = results
        self._last_run_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._last_run_date = date.today()

        ok = sum(1 for r in results if r["status"] == "ok")
        fail = len(results) - ok
        logger.info("每日入库完成: 成功=%d, 失败=%d", ok, fail)
        return {"results": results, "message": f"完成：成功 {ok} 条，失败 {fail} 条"}

    # ── Scheduler ──────────────────────────────────────────

    def start_scheduler(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._thread.start()
        logger.info("每日入库调度器已启动")

    def stop_scheduler(self):
        self._stop_event.set()
        logger.info("每日入库调度器已停止")

    def _scheduler_loop(self):
        while not self._stop_event.is_set():
            try:
                cfg = self.get_config()
                if cfg["enabled"]:
                    now = datetime.now()
                    if (
                        now.hour == cfg["hour"]
                        and now.minute == 0
                        and self._last_run_date != now.date()
                    ):
                        logger.info("每日入库定时触发: %s", now)
                        self.run_import()
            except Exception as e:
                logger.error("调度器异常: %s", e, exc_info=True)
            # 每 30 秒检查一次
            self._stop_event.wait(30)


_instance: GyDailyImportService | None = None


def get_gy_daily_import_service() -> GyDailyImportService:
    global _instance
    if _instance is None:
        _instance = GyDailyImportService()
    return _instance
