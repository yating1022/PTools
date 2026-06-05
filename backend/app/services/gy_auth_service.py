import logging
from typing import Any

from app.clients.gy_client import GuangyaAPI
from app.database import SessionLocal
from app.models.gy import GyAuth

logger = logging.getLogger(__name__)


def _get_or_create_auth(db) -> GyAuth:
    auth = db.query(GyAuth).first()
    if not auth:
        auth = GyAuth()
        db.add(auth)
        db.commit()
        db.refresh(auth)
    return auth


class GyAuthService:
    """光鸭网盘认证服务：短信登录 + Token 管理"""

    def __init__(self):
        with SessionLocal() as db:
            auth = _get_or_create_auth(db)
            self._access_token: str | None = auth.access_token or None
            self._refresh_token: str | None = auth.refresh_token or None
            self._phone: str | None = auth.phone or None
            self._device_id: str | None = auth.device_id or None
        # 会话级临时状态，不需要持久化
        self._captcha_token: str | None = None
        self._verification_id: str | None = None

    @property
    def is_authenticated(self) -> bool:
        return bool(self._access_token)

    def get_client(self) -> GuangyaAPI:
        if not self._access_token:
            raise ValueError("未登录，请先通过短信验证登录")
        return GuangyaAPI(
            access_token=self._access_token,
            refresh_token=self._refresh_token,
            device_id=self._device_id or None,
        )

    def get_status(self) -> dict[str, Any]:
        return {
            "authenticated": self.is_authenticated,
            "has_refresh_token": bool(self._refresh_token),
            "phone": self._phone,
        }

    def sms_init(self, phone_number: str, captcha_token: str | None = None) -> dict[str, Any]:
        if not phone_number:
            raise ValueError("手机号不能为空")

        self._phone = phone_number.strip()
        client = GuangyaAPI(device_id=self._device_id or None)
        try:
            result = client.login_sms_init(self._phone, captcha_token=captcha_token)
            self._captcha_token = result.get("captcha_token")
            self._device_id = client.device_id
            logger.debug("sms_init captcha_token acquired: %s", bool(self._captcha_token))
            return {
                "phone": self._phone,
                "captcha_token": self._captcha_token,
                "captcha_url": result.get("captcha_url"),
                "need_captcha": result.get("need_captcha", False),
            }
        finally:
            client.close()

    def sms_send(
        self,
        phone_number: str,
        captcha_token: str | None = None,
        target: str = "ANY",
    ) -> dict[str, Any]:
        token = captcha_token or self._captcha_token
        if not token:
            raise ValueError("请先初始化登录流程")

        phone = (phone_number or self._phone or "").strip()
        client = GuangyaAPI(device_id=self._device_id or None)
        try:
            result = client.login_sms_send(phone, token, target)
            self._verification_id = result.get("verification_id")
            return {
                "verification_id": self._verification_id,
                "message": "验证码已发送",
            }
        finally:
            client.close()

    def sms_verify(self, verification_code: str) -> dict[str, Any]:
        if not self._verification_id:
            raise ValueError("请先发送验证码")
        if not verification_code:
            raise ValueError("验证码不能为空")

        client = GuangyaAPI(device_id=self._device_id or None)
        try:
            result = client.login_sms_verify(self._verification_id, verification_code)
            return {
                "verification_token": result.get("verification_token"),
                "message": "验证码校验成功",
            }
        finally:
            client.close()

    def sms_signin(
        self,
        verification_code: str,
        verification_token: str,
        captcha_token: str | None = None,
    ) -> dict[str, Any]:
        if not self._phone:
            raise ValueError("请先初始化登录流程")

        token = captcha_token or self._captcha_token
        if not token:
            raise ValueError("captcha_token 缺失")

        client = GuangyaAPI(device_id=self._device_id or None)
        try:
            result = client.login_sms_signin(
                verification_code=verification_code,
                verification_token=verification_token,
                username=self._phone,
                captcha_token=token,
            )
            self._access_token = result.get("access_token")
            self._refresh_token = result.get("refresh_token")
            self._device_id = client.device_id
            self._persist()
            logger.info("登录成功: phone=%s", self._phone)
            return {
                "access_token": self._access_token,
                "refresh_token": self._refresh_token,
                "message": "登录成功",
            }
        finally:
            client.close()

    def refresh(self) -> dict[str, Any]:
        if not self._refresh_token:
            raise ValueError("无 refresh_token，请重新登录")

        client = GuangyaAPI(refresh_token=self._refresh_token, device_id=self._device_id or None)
        try:
            result = client.refresh()
            self._access_token = result.get("access_token")
            self._refresh_token = result.get("refresh_token", self._refresh_token)
            self._device_id = client.device_id
            self._persist()
            logger.info("Token 已刷新")
            return {"access_token": self._access_token, "message": "Token 已刷新"}
        finally:
            client.close()

    def get_user_info(self) -> dict[str, Any]:
        client = self.get_client()
        try:
            return client.user_info()
        finally:
            client.close()

    def _persist(self) -> None:
        with SessionLocal() as db:
            auth = _get_or_create_auth(db)
            auth.phone = self._phone or ""
            auth.access_token = self._access_token or ""
            auth.refresh_token = self._refresh_token or ""
            auth.device_id = self._device_id or ""
            db.commit()


_instance: GyAuthService | None = None


def get_gy_auth_service() -> GyAuthService:
    global _instance
    if _instance is None:
        _instance = GyAuthService()
    return _instance
