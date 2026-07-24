# api_gateway/main.py
import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(__file__))

import logging
import grpc
import asyncpg
import redis.asyncio as aioredis
from fastapi import FastAPI
from contextlib import asynccontextmanager

from config import GatewaySettings
from api_gateway.routers import auth
from shared.redis_cache import close as close_redis
from api_gateway.routers.playlists import router as playlists_router, user_playlists_router

from user_service.protos.generated import user_pb2, user_pb2_grpc
from playlist_service.protos.generated import playlist_pb2, playlist_pb2_grpc

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("gateway")
cfg = GatewaySettings()


def _to_asyncpg_url(url: str) -> str:
	return url.replace("postgresql+asyncpg://", "postgresql://")


@asynccontextmanager
async def lifespan(app: FastAPI):
	# === Startup ===
	log.info("Starting api-gateway...")

	# PostgreSQL (через asyncpg — нужен обычный URL)
	try:
		conn = await asyncpg.connect(_to_asyncpg_url(cfg.DATABASE_URL))
		await conn.fetchval("SELECT 1")
		await conn.close()
		log.info("Connected to PostgreSQL")
	except Exception as e:
		log.error(f"PostgreSQL connection failed: {e}")

	# Redis
	try:
		r = aioredis.from_url(cfg.REDIS_URL)
		await r.ping()
		await r.close()
		log.info("Connected to Redis")
	except Exception as e:
		log.error(f"Redis connection failed: {e}")

	yield

	# === Shutdown ===
	log.info("Shutting down api-gateway...")
	await close_redis()
	log.info("Api-gateway shutdown complete")


app = FastAPI(lifespan=lifespan)
app.include_router(auth.router)
app.include_router(playlists_router)
app.include_router(user_playlists_router)


@app.get("/health")
def health():
	return {"status": "ok", "service": "api-gateway"}


def _grpc_ping(url, stub_cls, req):
	ch = grpc.insecure_channel(url)
	try:
		resp = stub_cls(ch).Ping(req, timeout=2)
		return {"message": resp.message}
	except Exception as e:
		log.error(f"gRPC ping failed: {e}")
		return {"error": str(e)}
	finally:
		ch.close()


@app.get("/ping/user")
def ping_user():
	return _grpc_ping(cfg.USER_GRPC_URL, user_pb2_grpc.UserServiceStub, user_pb2.PingRequest())


@app.get("/ping/playlist")
def ping_playlist():
	return _grpc_ping(cfg.PLAYLIST_GRPC_URL, playlist_pb2_grpc.PlaylistServiceStub, playlist_pb2.PingRequest())



from fastapi.staticfiles import StaticFiles
import os

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/app", StaticFiles(directory=static_dir, html=True), name="static")