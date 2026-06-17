import sys
import os
import asyncio
import logging
import grpc
from concurrent import futures
from sqlalchemy import text

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from config import PlaylistServiceSettings
from shared.database import engine
from shared.models.user import Base
import shared.models.playlist  # noqa: F401
from shared.redis_cache import redis_client, close as close_redis
from kafka_producer import kafka_producer

from playlist_service.protos.generated import playlist_pb2_grpc
from grpc_playlist_servicer import PlaylistServiceServicer

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("playlist-service")
cfg = PlaylistServiceSettings()


async def init_db():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        log.info("Database initialized")
    except Exception as e:
        log.error(f"Failed to initialize database: {e}")
        raise


async def health_check():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        log.info("Connected to PostgreSQL")
    except Exception as e:
        log.error(f"PostgreSQL connection failed: {e}")
        raise
    try:
        await redis_client.ping()
        log.info("Connected to Redis")
    except Exception as e:
        log.error(f"Redis connection failed: {e}")
        raise


async def serve():
    server = None
    try:
        await health_check()
        await init_db()
        await kafka_producer.start()  # Теперь не падает, если Kafka недоступна

        server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
        playlist_pb2_grpc.add_PlaylistServiceServicer_to_server(PlaylistServiceServicer(), server)

        listen_addr = f"[::]:{cfg.GRPC_PORT}"
        server.add_insecure_port(listen_addr)
        log.info(f"Starting playlist-service on {listen_addr}")
        await server.start()
        await server.wait_for_termination()
    except KeyboardInterrupt:
        log.info("Received keyboard interrupt")
    except Exception as e:
        log.error(f"Server error: {e}")
        raise
    finally:
        log.info("Performing graceful shutdown...")
        if server:
            await server.stop(grace=5)
        await kafka_producer.close()
        await close_redis()
        await engine.dispose()
        log.info("Shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        log.info("Service stopped by user")
    except Exception as e:
        log.error(f"Fatal error: {e}")
        sys.exit(1)