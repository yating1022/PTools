import time

import jwt
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings

router = APIRouter(tags=["auth-gate"])

_ALGORITHM = "HS256"
_EXPIRE_SECONDS = 7 * 24 * 3600  # 7 天


class VerifyBody(BaseModel):
    secret_key: str


@router.post("/verify")
async def verify(body: VerifyBody):
    if body.secret_key != settings.app.secret_key:
        raise HTTPException(status_code=401, detail="密钥错误")

    now = int(time.time())
    payload = {
        "sub": "p-tools",
        "iat": now,
        "exp": now + _EXPIRE_SECONDS,
    }
    token = jwt.encode(payload, settings.app.secret_key, algorithm=_ALGORITHM)
    return {"token": token, "expires_in": _EXPIRE_SECONDS}
