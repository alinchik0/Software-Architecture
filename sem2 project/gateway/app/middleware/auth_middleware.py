from fastapi import Request, HTTPException
from app.core.security import verify_token

PUBLIC_PATHS = [
    "/",
    "/health",
    "/auth",   # всё что начинается с /auth — без проверки
]


async def auth_middleware(request: Request, call_next):
    path = request.url.path

    # пропускаем публичные роуты
    if any(path.startswith(p) for p in PUBLIC_PATHS):
        return await call_next(request)

    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid auth scheme")

        payload = verify_token(token)

        # сохраняем пользователя в request.state
        request.state.user = payload

    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Authorization header")

    return await call_next(request)