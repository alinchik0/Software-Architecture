# shared/events.py
import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any
from confluent_kafka import Producer
from .config import get_settings

logger = logging.getLogger(__name__)

def build_event(event_type: str, aggregate_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "version": "1.0",
        "timestamp": datetime.now(UTC).isoformat(),
        "aggregate_id": aggregate_id,
        "payload": payload,
    }

class KafkaProducer:
    def __init__(self) -> None:
        self._producer = Producer({"bootstrap.servers": get_settings().kafka_bootstrap_servers})

    async def publish(self, topic: str, key: str, event: dict[str, Any]) -> None:
        data = json.dumps(event).encode()
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                self._producer.produce(topic, key=key.encode(), value=data)
                self._producer.flush(5)
                return
            except Exception as exc:
                last_error = exc
                import asyncio
                await asyncio.sleep(0.2 * (2**attempt))
        logger.error("kafka_publish_failed", extra={"topic": topic, "error": str(last_error)})
        raise RuntimeError("Kafka publish failed") from last_error
