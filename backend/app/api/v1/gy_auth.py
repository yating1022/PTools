import logging
from typing import Any

from fastapi import APIRouter, Form, HTTPException

from app.dependencies import GyAuthDep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gy/auth", tags=["gy-auth"])


def _safe_call(fn, *args, **kwargs) -> dict[str, Any]:
    try:
        return fn(*args, **kwargs)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("GyAuth error: %s", e)
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/status")
async def auth_status(auth: GyAuthDep):
    return auth.get_status()


@router.post("/sms/init")
async def sms_init(
    auth: GyAuthDep,
    phone_number: str = Form(..., description="手机号，如 +8613800138000"),
    captcha_token: str | None = Form(None, description="验证码 token（可选，验证码通过后传入）"),
):
    return _safe_call(auth.sms_init, phone_number, captcha_token)


@router.post("/sms/send")
async def sms_send(
    auth: GyAuthDep,
    phone_number: str = Form(..., description="手机号"),
    captcha_token: str | None = Form(None),
    target: str = Form("ANY"),
):
    return _safe_call(auth.sms_send, phone_number, captcha_token, target)


@router.post("/sms/verify")
async def sms_verify(
    auth: GyAuthDep,
    verification_code: str = Form(..., description="短信验证码"),
):
    return _safe_call(auth.sms_verify, verification_code)


@router.post("/sms/signin")
async def sms_signin(
    auth: GyAuthDep,
    verification_code: str = Form(...),
    verification_token: str = Form(...),
    captcha_token: str | None = Form(None),
):
    return _safe_call(
        auth.sms_signin, verification_code, verification_token, captcha_token
    )


@router.post("/refresh")
async def refresh_token(auth: GyAuthDep):
    return _safe_call(auth.refresh)


@router.get("/user")
async def get_user_info(auth: GyAuthDep):
    return _safe_call(auth.get_user_info)
