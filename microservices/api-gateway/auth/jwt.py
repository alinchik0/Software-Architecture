# api-gateway/auth/jwt.py
import time
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from shared.config import get_settings
from shared.security import decode_token

bearer = HTTPBearer(auto_error=True)

async def redis_client() -> Redis:
    return Redis.from_url(get_settings().redis_url, decode_responses=True)

async def current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> str:
    payload = decode_token(creds.credentials)
    if payload.get("typ") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid token type")
    redis = await redis_client()
    if await redis.get(f"blacklist:{payload['jti']}"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "token blacklisted")
    return str(payload["sub"])

async def blacklist_token(token: str) -> None:
    payload = decode_token(token)
    ttl = max(0, int(payload["exp"]) - int(time.time()))
    redis = await redis_client()
    await redis.setex(f"blacklist:{payload['jti']}", ttl, "1")
