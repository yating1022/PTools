"""
光鸭网盘 API 客户端（逆向自 guangyapan.com 真实接口）

所有接口通过 Chrome DevTools 逆向抓包获得，修复了 guangyaclient 库的以下问题：
- fs_files → 应为 get_file_list（guangyaclient 用了错误的端点名）
- fs_create_dir → 应为 create_dir
- fs_delete → 应为 delete_file
- parentId 应为 string 类型，不是 int
- user_info 应为 GET 请求，不是 POST

API 路径前缀：
- 文件操作：/userres/v1/...
- 云下载：/cloudcollection/v1/...  /cloudcollection/v2/...
"""

from __future__ import annotations

import logging
import time
from secrets import token_hex
from typing import Any

import httpx

logger = logging.getLogger(__name__)

API_BASE = "https://api.guangyapan.com"
ACCOUNT_BASE = "https://account.guangyapan.com"
CLIENT_ID = "aMe-8VSlkrbQXpUR"


def _traceparent() -> str:
    """Generate a traceparent header value (matches web app format)."""
    import random
    trace_id = f"{random.getrandbits(128):032x}"
    span_id = f"{random.getrandbits(64):016x}"
    return f"00-{trace_id}-{span_id}-01"


def _did() -> str:
    """Generate a device ID (32-char hex)."""
    return token_hex(16)


class GuangyaAPI:
    """
    光鸭网盘 API 客户端

    所有方法直接对应 guangyapan.com 逆向抓包到的真实接口。
    """

    def __init__(
        self,
        access_token: str = "",
        refresh_token: str = "",
        device_id: str | None = None,
    ):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.device_id = device_id or _did()
        self._token_expires_at: float | None = None
        self._http = httpx.Client(timeout=30)

    def close(self):
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    # ── Headers ──────────────────────────────────────────────────────

    def _api_headers(self) -> dict[str, str]:
        """Headers for api.guangyapan.com requests."""
        return {
            "accept": "application/json, text/plain, */*",
            "authorization": f"Bearer {self.access_token}",
            "content-type": "application/json",
            "did": self.device_id,
            "dt": "4",
            "origin": "https://www.guangyapan.com",
            "referer": "https://www.guangyapan.com/",
            "traceparent": _traceparent(),
            "user-agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/147.0.0.0 Safari/537.36"
            ),
        }

    def _account_headers(self) -> dict[str, str]:
        """Headers for account.guangyapan.com requests."""
        return {
            "accept": "*/*",
            "content-type": "application/json",
            "origin": "https://www.guangyapan.com",
            "referer": "https://www.guangyapan.com/",
            "user-agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/147.0.0.0 Safari/537.36"
            ),
            "x-client-id": CLIENT_ID,
            "x-client-version": "0.0.1",
            "x-device-id": self.device_id,
            "x-device-model": "chrome%2F147.0.0.0",
            "x-device-name": "PC-Chrome",
            "x-device-sign": f"wdi10.{self.device_id}{token_hex(16)}",
            "x-net-work-type": "NONE",
            "x-os-version": "Win32",
            "x-platform-version": "1",
            "x-protocol-version": "301",
            "x-provider-name": "NONE",
            "x-sdk-version": "9.0.2",
        }

    # ── Internal helpers ─────────────────────────────────────────────

    def _post(self, path: str, body: dict, allow_codes: list[int] | None = None) -> dict:
        """POST to api.guangyapan.com with auto token refresh."""
        self._maybe_refresh()
        url = f"{API_BASE}{path}"
        r = self._http.post(url, headers=self._api_headers(), json=body)
        if r.status_code == 401 and self.refresh_token:
            self.refresh()
            r = self._http.post(url, headers=self._api_headers(), json=body)
        if r.status_code >= 400:
            try:
                err_body = r.json()
            except Exception:
                err_body = r.text
            raise Exception(f"API {r.status_code} {path}: {err_body}")
        data = r.json()
        code = data.get("code", 0)
        if code and code != 0 and (not allow_codes or code not in allow_codes):
            raise Exception(f"API error: {data}")
        return data

    def _maybe_refresh(self):
        """Refresh token if expired."""
        if self._token_expires_at and time.time() >= self._token_expires_at:
            self.refresh()

    # ── Auth ─────────────────────────────────────────────────────────

    def refresh(self) -> dict[str, Any]:
        """刷新 access_token（POST /v1/auth/token）"""
        if not self.refresh_token:
            raise Exception("无 refresh_token")
        headers = self._account_headers()
        headers["x-action"] = "401"
        r = self._http.post(
            f"{ACCOUNT_BASE}/v1/auth/token",
            headers=headers,
            json={
                "client_id": CLIENT_ID,
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
            },
        )
        if r.status_code >= 400:
            try:
                err_body = r.json()
            except Exception:
                err_body = r.text
            raise Exception(f"Auth {r.status_code} refresh: {err_body}")
        result = r.json()
        self.access_token = result["access_token"]
        self.refresh_token = result.get("refresh_token", self.refresh_token)
        expires_in = result.get("expires_in")
        if expires_in:
            self._token_expires_at = time.time() + expires_in
        return result

    def user_info(self) -> dict[str, Any]:
        """获取当前用户信息（GET /v1/user/me）"""
        self._maybe_refresh()
        headers = self._account_headers()
        headers["authorization"] = f"Bearer {self.access_token}"
        r = self._http.get(
            f"{ACCOUNT_BASE}/v1/user/me",
            headers=headers,
        )
        if r.status_code == 401 and self.refresh_token:
            self.refresh()
            headers["authorization"] = f"Bearer {self.access_token}"
            r = self._http.get(f"{ACCOUNT_BASE}/v1/user/me", headers=headers)
        if r.status_code >= 400:
            try:
                err_body = r.json()
            except Exception:
                err_body = r.text
            raise Exception(f"Auth {r.status_code} user_info: {err_body}")
        return r.json()

    # ── Captcha ─────────────────────────────────────────────────────

    # ── SMS Login ────────────────────────────────────────────────────

    def login_sms_init(self, phone_number: str, captcha_token: str | None = None) -> dict:
        """短信登录 Step 1: 初始化（POST /v1/shield/captcha/init）"""
        headers = self._account_headers()
        body: dict[str, Any] = {
            "client_id": CLIENT_ID,
            "action": "POST:/v1/auth/verification",
            "device_id": self.device_id,
            "meta": {"phone_number": phone_number},
        }
        if captcha_token:
            body["captcha_token"] = captcha_token
        r = self._http.post(
            f"{ACCOUNT_BASE}/v1/shield/captcha/init",
            headers=headers,
            json=body,
        )
        if r.status_code >= 400:
            try:
                err_body = r.json()
            except Exception:
                err_body = r.text
            raise Exception(f"Auth {r.status_code} login_sms_init: {err_body}")
        return r.json()

    def login_sms_send(self, phone_number: str, captcha_token: str = "", target: str = "ANY") -> dict:
        """短信登录 Step 2: 发送验证码"""
        headers = self._account_headers()
        if captcha_token:
            headers["x-captcha-token"] = captcha_token
        r = self._http.post(
            f"{ACCOUNT_BASE}/v1/auth/verification",
            headers=headers,
            json={
                "phone_number": phone_number,
                "target": target,
                "client_id": CLIENT_ID,
            },
        )
        if r.status_code >= 400:
            try:
                err_body = r.json()
            except Exception:
                err_body = r.text
            raise Exception(f"Auth {r.status_code} login_sms_send: {err_body}")
        return r.json()

    def login_sms_verify(self, verification_id: str, verification_code: str) -> dict:
        """短信登录 Step 3: 验证验证码"""
        r = self._http.post(
            f"{ACCOUNT_BASE}/v1/auth/verification/verify",
            headers=self._account_headers(),
            json={
                "verification_id": verification_id,
                "verification_code": verification_code,
                "client_id": CLIENT_ID,
            },
        )
        if r.status_code >= 400:
            try:
                err_body = r.json()
            except Exception:
                err_body = r.text
            raise Exception(f"Auth {r.status_code} login_sms_verify: {err_body}")
        return r.json()

    def login_sms_signin(
        self,
        verification_code: str,
        verification_token: str,
        username: str,
        captcha_token: str,
    ) -> dict:
        """短信登录 Step 4: 完成登录"""
        headers = self._account_headers()
        headers["x-captcha-token"] = captcha_token
        r = self._http.post(
            f"{ACCOUNT_BASE}/v1/auth/signin",
            headers=headers,
            json={
                "verification_code": verification_code,
                "verification_token": verification_token,
                "username": username,
                "client_id": CLIENT_ID,
            },
        )
        if r.status_code >= 400:
            try:
                err_body = r.json()
            except Exception:
                err_body = r.text
            raise Exception(f"Auth {r.status_code} login_sms_signin: {err_body}")
        result = r.json()
        self.access_token = result.get("access_token", "")
        self.refresh_token = result.get("refresh_token", self.refresh_token)
        expires_in = result.get("expires_in")
        if expires_in:
            self._token_expires_at = time.time() + expires_in
        return result

    # ── File Operations ──────────────────────────────────────────────

    def get_file_list(
        self,
        parent_id: str = "",
        page_size: int = 50,
        order_by: int = 3,
        sort_type: int = 1,
        file_types: list | None = None,
    ) -> dict:
        """
        获取文件列表

        POST /nd.bizuserres.s/v1/file/get_file_list

        :param parent_id: 父文件夹 ID，空字符串表示根目录
        :param page_size: 每页数量
        :param order_by: 排序字段（3 = 修改时间）
        :param sort_type: 排序方式（0 升序, 1 降序）
        :param file_types: 文件类型过滤
        """
        body: dict[str, Any] = {
            "parentId": str(parent_id),
            "pageSize": page_size,
            "orderBy": order_by,
            "sortType": sort_type,
        }
        if file_types is not None:
            body["fileTypes"] = file_types
        return self._post("/userres/v1/file/get_file_list", body)

    def create_dir(self, dir_name: str, parent_id: str = "") -> dict:
        """
        创建文件夹

        POST /nd.bizuserres.s/v1/file/create_dir

        :param dir_name: 文件夹名称
        :param parent_id: 父文件夹 ID
        """
        return self._post("/userres/v1/file/create_dir", {
            "parentId": str(parent_id),
            "dirName": dir_name,
            "failIfNameExist": True,
        }, allow_codes=[159])

    def delete_file(self, file_ids: list[str]) -> dict:
        """
        删除文件/文件夹

        POST /nd.bizuserres.s/v1/file/delete_file

        :param file_ids: 文件 ID 列表
        """
        return self._post("/userres/v1/file/delete_file", {
            "fileIds": file_ids,
        })

    def get_task_status(self, task_id: str) -> dict:
        """
        查询文件操作任务状态

        POST /userres/v1/get_task_status

        :param task_id: 任务 ID（delete_file 等操作返回）
        """
        return self._post("/userres/v1/get_task_status", {
            "taskId": task_id,
        })

    def get_res_download_url(self, file_id: str) -> dict:
        """
        获取文件下载链接

        POST /nd.bizuserres.s/v1/get_res_download_url

        :param file_id: 文件 ID
        """
        return self._post("/userres/v1/get_res_download_url", {
            "fileId": file_id,
        })

    def rename(self, file_id: str, new_name: str) -> dict:
        """
        重命名文件/文件夹

        POST /nd.bizuserres.s/v1/file/rename

        :param file_id: 文件 ID
        :param new_name: 新名称
        """
        return self._post("/userres/v1/file/rename", {
            "fileId": file_id,
            "newName": new_name,
        })

    def move_file(self, file_ids: list[str], parent_id: str) -> dict:
        """
        移动文件

        POST /nd.bizuserres.s/v1/file/move_file

        :param file_ids: 文件 ID 列表
        :param parent_id: 目标文件夹 ID
        """
        return self._post("/userres/v1/file/move_file", {
            "fileIds": file_ids,
            "parentId": str(parent_id),
        })

    def copy_file(self, file_ids: list[str], parent_id: str) -> dict:
        """
        复制文件

        POST /nd.bizuserres.s/v1/file/copy_file

        :param file_ids: 文件 ID 列表
        :param parent_id: 目标文件夹 ID
        """
        return self._post("/userres/v1/file/copy_file", {
            "fileIds": file_ids,
            "parentId": str(parent_id),
        })

    def resolve_res(self, url: str) -> dict:
        """
        云下载：解析链接（仅解析，不创建下载任务）

        POST /cloudcollection/v1/resolve_res

        :param url: 下载链接（HTTP/HTTPS/magnet/ed2k）
        """
        return self._post("/cloudcollection/v1/resolve_res", {
            "url": url,
        })

    def create_cloud_task(
        self,
        url: str,
        parent_id: str = "",
        new_name: str | None = None,
        file_indexes: list[int] | None = None,
    ) -> dict:
        """
        云下载：创建下载任务

        POST /cloudcollection/v1/create_task

        :param url: 下载链接
        :param parent_id: 目标文件夹 ID（空字符串表示根目录）
        :param new_name: 保存后的文件名
        :param file_indexes: BT 子文件索引列表（仅 magnet/ed2k 需要）
        """
        body: dict[str, Any] = {
            "url": url,
            "parentId": str(parent_id),
        }
        if new_name is not None:
            body["newName"] = new_name
        if file_indexes is not None:
            body["fileIndexes"] = file_indexes
        return self._post("/cloudcollection/v1/create_task", body)

    def list_cloud_tasks(self, status: list[int] | None = None, page_size: int = 50) -> dict:
        """
        云下载：查询任务列表

        POST /cloudcollection/v1/list_task

        状态码：1=等待中 2=下载中 3=已完成 5=失败

        :param status: 状态过滤列表，None 返回全部
        :param page_size: 每页数量
        """
        body: dict[str, Any] = {"pageSize": page_size}
        if status is not None:
            body["status"] = status
        return self._post("/cloudcollection/v1/list_task", body)

    def retry_cloud_task(self, task_id: str) -> dict:
        """
        云下载：重试失败任务

        POST /cloudcollection/v2/retry_task
        """
        return self._post("/cloudcollection/v2/retry_task", {"taskId": task_id})

    def delete_cloud_task(self, task_ids: list[str]) -> dict:
        """
        云下载：删除任务

        POST /cloudcollection/v2/delete_task
        """
        return self._post("/cloudcollection/v2/delete_task", {"taskIds": task_ids})

    def get_file_detail(self, file_id: str) -> dict:
        """
        获取文件详情

        POST /nd.bizuserres.s/v1/file/get_file_detail

        :param file_id: 文件 ID
        """
        return self._post("/userres/v1/file/get_file_detail", {
            "fileId": file_id,
        })

    # ── Share Operations ──────────────────────────────────────────────

    def get_share_access_token(self, share_id: str, code: str = "") -> str:
        """
        获取分享链接的 accessToken

        POST /userres/v1/get_share_access_token

        :param share_id: 分享 ID（URL 中 /s/ 后的部分）
        :param code: 提取码（可选）
        :return: accessToken JWT
        """
        body: dict[str, str] = {"shareId": share_id}
        if code:
            body["code"] = code
        result = self._post("/userres/v1/get_share_access_token", body)
        return result.get("data", {}).get("accessToken", "")

    def get_share_files(self, access_token: str, parent_id: str = "", page_size: int = 50) -> dict:
        """
        获取分享链接中的文件列表

        POST /userres/v1/get_share_page_files_list

        :param access_token: 分享 accessToken
        :param parent_id: 父文件夹 ID（空表示根目录）
        :param page_size: 每页数量
        """
        return self._post("/userres/v1/get_share_page_files_list", {
            "pageSize": page_size,
            "accessToken": access_token,
            "parentId": str(parent_id),
            "orderBy": 0,
            "sortType": 0,
        })

    def restore_share(
        self,
        access_token: str,
        file_ids: list[str],
        parent_id: str = "",
    ) -> dict:
        """
        保存分享文件到自己的网盘

        POST /userres/v1/restore_share

        :param access_token: 分享 accessToken
        :param file_ids: 要保存的文件 ID 列表
        :param parent_id: 目标文件夹 ID
        """
        return self._post("/userres/v1/restore_share", {
            "accessToken": access_token,
            "fileIds": file_ids,
            "parentId": str(parent_id),
        })
