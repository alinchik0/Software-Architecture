# playlist-service/main.py
import sys, os, json, logging, asyncio, grpc, threading
from concurrent import futures
from confluent_kafka import Consumer
import asyncpg

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import PlaylistServiceSettings
from protos.generated import playlist_pb2, playlist_pb2_grpc

logging.basicConfig(level=logging.INFO); log = logging.getLogger("playlist-service")
cfg = PlaylistServiceSettings(); stop_event = threading.Event()

class PlaylistServicer(playlist_pb2_grpc.PlaylistServiceServicer):
    def Ping(self, request, context):
        return playlist_pb2.PingResponse(message="pong from playlist-service")

def _kafka_loop():
    c = None
    try:
        c = Consumer({'bootstrap.servers': cfg.KAFKA_SERVERS, 'group.id': 'playlist-grp', 'auto.offset.reset': 'earliest'})
        c.subscribe([cfg.KAFKA_TOPIC]); log.info("Subscribed to user.events")
        while not stop_event.is_set():
            msg = c.poll(1.0)
            if msg and msg.error() is None:
                data = json.loads(msg.value().decode()); log.info(f"Received event: {data.get('event_type')} - {data.get('payload')}")
    except Exception as e: log.warning(f"Kafka loop stopped: {e}")
    finally:
        if c: c.close()

async def _init():
    try:
        c = await asyncpg.connect(cfg.DATABASE_URL)
        await c.fetchval("SELECT 1"); await c.close()
        log.info("Connected to PostgreSQL")
    except Exception as e: log.error(f"DB fail: {e}")
    try:
        import redis; redis.Redis.from_url(cfg.REDIS_URL).ping(); log.info("Connected to Redis")
    except Exception as e: log.error(f"Redis fail: {e}")

def run():
    asyncio.run(_init())
    threading.Thread(target=_kafka_loop, daemon=True).start()

    srv = grpc.server(futures.ThreadPoolExecutor(10))
    playlist_pb2_grpc.add_PlaylistServiceServicer_to_server(PlaylistServicer(), srv)
    srv.add_insecure_port(f"[::]:{cfg.GRPC_PORT}")
    srv.start(); log.info(f"playlist-service started on port {cfg.GRPC_PORT}")
    try: srv.wait_for_termination()
    except KeyboardInterrupt: stop_event.set(); log.info("Shutdown..."); srv.stop(0)
if __name__ == "__main__": run()