# worker-service/handlers/playlist.py
import json
from redis.asyncio import Redis

async def invalidate_playlist_cache(redis: Redis, event: dict) -> None:
    if event.get("event_type", "").startswith("playlist."):
        await redis.delete(f"playlist:{event['aggregate_id']}")
