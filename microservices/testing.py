import asyncio
import logging
from aiokafka import AIOKafkaConsumer

logging.basicConfig(
	level=logging.INFO,
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger("kafka-monitor")


async def monitor():
	# Use 'kafka:29092' if running inside docker-compose network
	# Use 'localhost:9092' if running directly on host machine
	bootstrap_servers = "localhost:9092"

	consumer = AIOKafkaConsumer(
		"music_events",
		bootstrap_servers=bootstrap_servers,
		value_deserializer=lambda v: v.decode("utf-8"),
		auto_offset_reset="earliest",
		group_id="monitor-group"
	)

	await consumer.start()
	log.info("[MONITOR] Started. Waiting for messages on topic 'music_events'...")

	try:
		async for msg in consumer:
			log.info(f"[MONITOR] RECEIVED: {msg.value}")
	except KeyboardInterrupt:
		log.info("[MONITOR] Stopping...")
	finally:
		await consumer.stop()


if __name__ == "__main__":
	asyncio.run(monitor())