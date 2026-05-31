# api-gateway/main.py
import logging
from fastapi import FastAPI, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from routes.auth import router as auth_router
from routes.users import router as users_router
from routes.playlists import router as playlists_router

logging.basicConfig(level=logging.INFO, format='{"level":"%(levelname)s","message":"%(message)s"}')
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="api-gateway")
app.state.limiter = limiter
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(playlists_router)

@app.get("/health")
@limiter.limit("60/minute")
async def health(request: Request) -> dict[str, str]:
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
