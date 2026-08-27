# import json
# import uuid
# import logging
# from datetime import datetime, timezone
# from typing import Any, Dict
#
# from aiokafka import AIOKafkaProducer
# from config import PlaylistServiceSettings
#
# log = logging.getLogger("playlist-service.kafka")
# cfg = PlaylistServiceSettings()
#
#
# class PlaylistKafkaProducer:
#     def __init__(self):
#         self.producer: AIOKafkaProducer | None = None
#         self._available = False
#
#     async def start(self) -> None:
#         try:
#             self.producer = AIOKafkaProducer(
#                 bootstrap_servers=cfg.KAFKA_BOOTSTRAP_SERVERS,
#                 value_serializer=lambda v: json.dumps(v).encode("utf-8"),
#                 request_timeout_ms=5000,
#             )
#             await self.producer.start()
#             self._available = True
#             log.info(f"Kafka producer started, topic={cfg.KAFKA_TOPIC}")
#         except Exception as e:
#             log.warning(f"Kafka unavailable, events will not be published: {e}")
#             self._available = False
#             self.producer = None
#
#     async def publish(self, event_type: str, playlist_id: int, user_id: int, payload: Dict[str, Any]) -> None:
#         if not self._available or not self.producer:
#             log.debug(f"Kafka unavailable, skipping event {event_type}")
#             return
#
#         event = {
#             "event_id": str(uuid.uuid4()),
#             "event_type": event_type,
#             "timestamp": datetime.now(timezone.utc).isoformat(),
#             "playlist_id": playlist_id,
#             "user_id": user_id,
#             "payload": payload,
#         }
#         try:
#             await self.producer.send_and_wait(cfg.KAFKA_TOPIC, value=event)
#             log.info(f"Published event {event_type} for playlist {playlist_id}")
#         except Exception as e:
#             log.warning(f"Failed to publish Kafka event: {e}")
#
#     async def close(self) -> None:
#         if self.producer:
#             try:
#                 await self.producer.stop()
#                 log.info("Kafka producer stopped")
#             except Exception as e:
#                 log.warning(f"Error stopping Kafka producer: {e}")
#
#
# kafka_producer = PlaylistKafkaProducer()

import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from aiokafka import AIOKafkaProducer
from config import settings

log = logging.getLogger("kafka-producer")

class KafkaProducer:
    def __init__(self):
        self.topic = settings.KAFKA_TOPIC
        self.bootstrap_servers = settings.KAFKA_BOOTSTRAP_SERVERS
        self.producer: AIOKafkaProducer | None = None
        self._is_ready = False

    async def start(self) -> None:
        try:
            log.info(f"[KAFKA] Connecting to broker at {self.bootstrap_servers}...")
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                request_timeout_ms=5000,
            )
            await self.producer.start()
            self._is_ready = True
            log.info(f"[KAFKA] Producer successfully started. Topic: '{self.topic}'")
        except Exception as e:
            log.error(f"[KAFKA] Failed to start producer: {e}. Events will be skipped (non-blocking).")
            self._is_ready = False
            self.producer = None

    async def publish(self, event_type: str, payload: Dict[str, Any]) -> None:
        if not self._is_ready or not self.producer:
            log.debug(f"[KAFKA] Unavailable, skipping event: {event_type}")
            return

        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
        try:
            await self.producer.send_and_wait(self.topic, value=event)
            log.info(f"[KAFKA] Published event '{event_type}' to topic '{self.topic}'")
        except Exception as e:
            log.error(f"[KAFKA] Failed to publish event: {e}")

    async def close(self) -> None:
        if self.producer:
            try:
                await self.producer.stop()
                log.info("[KAFKA] Producer stopped")
            except Exception as e:
                log.warning(f"[KAFKA] Error stopping producer: {e}")

# Global instance
kafka_producer = KafkaProducer()