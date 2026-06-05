import logging
from typing import Any

from app.clients.gy_client import GuangyaAPI
from app.services.gy_auth_service import GyAuthService, get_gy_auth_service

logger = logging.getLogger(__name__)


def _transform_file(raw: dict[str, Any]) -> dict[str, Any]:
    is_dir = raw.get("dirType") == 1 and raw.get("resType") == 2
    ext = raw.get("ext", "")
    mime_type = raw.get("mineType", "")
    file_type = (
        "folder"
        if is_dir
        else _guess_type(raw.get("resType", 0), raw.get("fileType", 0), ext, mime_type)
    )
    size = raw.get("fileSize", 0)
    if size and size < 0:
        size = 0
    return {
        "file_id": str(raw.get("fileId", "")),
        "name": raw.get("fileName", ""),
        "type": file_type,
        "size": size,
        "created_at": str(raw.get("ctime", "")),
        "updated_at": str(raw.get("utime", "")),
        "ext": ext.lstrip(".") if ext else "",
        "mime_type": mime_type,
        "thumbnail": raw.get("thumbnail", ""),
    }


def _guess_type(res_type: int, file_type: Any = 0, ext: str = "", mime_type: str = "") -> str:
    if ext:
        ext = ext.lower().lstrip(".")
        if ext in ("jpg", "jpeg", "png", "gif", "bmp", "webp", "svg", "ico", "tiff"):
            return "image"
        if ext in ("mp4", "mkv", "avi", "mov", "wmv", "flv", "rmvb", "ts", "m4v", "webm"):
            return "video"
        if ext in ("mp3", "wav", "flac", "aac", "ogg", "wma", "m4a", "opus"):
            return "audio"
        if ext in ("pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "csv", "rtf"):
            return "document"
        if ext in ("zip", "rar", "7z", "tar", "gz", "bz2", "xz"):
            return "archive"
        if ext in ("srt", "ass", "ssa", "sub", "vtt"):
            return "subtitle"
        if ext in ("iso", "img", "nrg"):
            return "disc"
    if mime_type:
        mt = mime_type.lower()
        if mt.startswith("image/"):
            return "image"
        if mt.startswith("video/"):
            return "video"
        if mt.startswith("audio/"):
            return "audio"
        if mt.startswith("text/") or mt.startswith("application/pdf"):
            return "document"
        if mt.startswith("application/zip") or mt.startswith("application/x-rar"):
            return "archive"
    ft_mapping = {1: "image", 2: "video", 3: "audio", 4: "document", 5: "archive"}
    if isinstance(file_type, int) and file_type in ft_mapping:
        return ft_mapping[file_type]
    if res_type == 2:
        return "folder"
    return "file"


class GyFileService:
    """光鸭网盘文件服务"""

    def __init__(self, auth_service: GyAuthService):
        self._auth = auth_service

    def _get_client(self) -> GuangyaAPI:
        return self._auth.get_client()

    def list_files(
        self,
        parent_id: str = "",
        file_type: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        client = self._get_client()
        try:
            result = client.get_file_list(parent_id, page_size)
            data = result.get("data", {})
            raw_files = data.get("list", data.get("files", []))
            files = [_transform_file(f) for f in raw_files]
            if file_type:
                files = [f for f in files if f["type"] == file_type]
            return {
                "files": files,
                "total": data.get("total", len(files)),
                "page": page,
                "page_size": page_size,
            }
        finally:
            client.close()

    def get_file(self, file_id: str) -> dict:
        client = self._get_client()
        try:
            return client.get_file_detail(file_id)
        finally:
            client.close()

    def get_download_url(self, file_id: str) -> str:
        client = self._get_client()
        try:
            result = client.get_res_download_url(file_id)
            data = result.get("data", {})
            return data.get("downloadUrl", data.get("url", ""))
        finally:
            client.close()

    def cloud_download(self, url: str, parent_id: str = "") -> dict:
        from app.database import SessionLocal
        from app.models.gy import GyConfig
        folder = parent_id
        if not folder:
            with SessionLocal() as db:
                cfg = db.query(GyConfig).filter(GyConfig.key == "cloud_download_folder").first()
                folder = cfg.value if cfg else ""
        client = self._get_client()
        try:
            return client.create_cloud_task(url, folder)
        finally:
            client.close()

    def list_cloud_tasks(
        self, status: list[int] | None = None, page_size: int = 50
    ) -> dict:
        client = self._get_client()
        try:
            return client.list_cloud_tasks(status, page_size)
        finally:
            client.close()

    def retry_cloud_task(self, task_id: str) -> dict:
        client = self._get_client()
        try:
            return client.retry_cloud_task(task_id)
        finally:
            client.close()

    def delete_cloud_task(self, task_ids: list[str]) -> dict:
        client = self._get_client()
        try:
            return client.delete_cloud_task(task_ids)
        finally:
            client.close()


_instance: GyFileService | None = None


def get_gy_file_service() -> GyFileService:
    global _instance
    if _instance is None:
        _instance = GyFileService(get_gy_auth_service())
    return _instance
