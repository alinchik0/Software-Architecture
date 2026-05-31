# worker-service/main.py
import asyncio
import json
import logging
import signal
import uuid
from confluent_kafka import Consumer, Producer
from redis.asyncio import Redis
from sqlalchemy.exc import IntegrityError
from shared.config import get_settings
from shared.db import SessionLocal
from shared.models import KafkaEvent
from handlers.playlist import invalidate_playlist_cache

logging.basicConfig(level=logging.INFO, format='{"level":"%(levelname)s","message":"%(message)s"}')
logger = logging.getLogger(__name__)

class Worker:
    def __init__(self) -> None:
        s = get_settings()
        self.consumer = Consumer({"bootstrap.servers": s.kafka_bootstrap_servers, "group.id": "worker-service", "auto.offset.reset": "earliest", "enable.auto.commit": False})
        self.producer = Producer({"bootstrap.servers": s.kafka_bootstrap_servers})
        self.redis = Redis.from_url(s.redis_url, decode_responses=True)
        self.running = True

    async def already_processed(self, topic: str, event_id: str) -> bool:
        async with SessionLocal() as session:
            session.add(KafkaEvent(event_id=uuid.UUID(event_id), topic=topic))
            try:
                await session.commit()
                return False
            except IntegrityError:
                await session.rollback()
                return True

    async def handle(self, topic: str, event: dict) -> None:
        if await self.already_processed(topic, event["event_id"]):
            return
        if topic == "playlist.events":
            await invalidate_playlist_cache(self.redis, event)

    async def run(self) -> None:
        self.consumer.subscribe(["user.events", "playlist.events"])
        while self.running:
            msg = self.consumer.poll(0.5)
            if msg is None:
                await asyncio.sleep(0)
                continue
            if msg.error():
                logger.error("kafka_consumer_error", extra={"error": str(msg.error())})
                continue
            try:
                event = json.loads(msg.value().decode())
                await self.handle(msg.topic(), event)
                self.consumer.commit(msg)
            except Exception as exc:
                logger.exception("critical_event_error")
                self.producer.produce(f"{msg.topic()}.dlq", key=msg.key(), value=msg.value())
                self.producer.flush(5)
                self.consumer.commit(msg)
        self.consumer.close()
        await self.redis.aclose()

async def main() -> None:
    worker = Worker()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: setattr(worker, "running", False))
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
