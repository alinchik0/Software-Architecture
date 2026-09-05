import sys
import os
import asyncio
import json
import logging
import grpc

# Добавляем корень проекта в путь для импорта shared и catalog_service
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
	sys.path.insert(0, ROOT)

from aiokafka import AIOKafkaConsumer
from sqlalchemy import select

from shared.database import async_session_factory
from shared.models.playlist import PlaylistTrack
from catalog_service import catalog_pb2, catalog_pb2_grpc
from config import settings

log = logging.getLogger("playlist-service.consumer")

# Глобальные переменные для gRPC клиента (ленивая инициализация)
_catalog_channel = None
_catalog_stub = None


def get_catalog_stub():
	global _catalog_channel, _catalog_stub
	if _catalog_channel is None:
		log.info("Connecting to catalog-service:50053")
		_catalog_channel = grpc.aio.insecure_channel('catalog-service:50053')
		_catalog_stub = catalog_pb2_grpc.CatalogServiceStub(_catalog_channel)
	return _catalog_stub


async def enrichment_consumer_task():
	"""
	Фоновая задача: слушает Kafka и асинхронно обогащает метаданные треков.
	"""
	try:
		log.info("Starting enrichment consumer task")
		log.info("Configuration: topic=%s, bootstrap=%s", settings.KAFKA_TOPIC, settings.KAFKA_BOOTSTRAP_SERVERS)

		consumer = AIOKafkaConsumer(
			settings.KAFKA_TOPIC,
			bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
			group_id='playlist-enrichment-group',
			auto_offset_reset='latest',
			value_deserializer=lambda v: json.loads(v.decode('utf-8'))
		)

		await consumer.start()
		log.info("Enrichment Consumer started, listening to topic: %s", settings.KAFKA_TOPIC)
		log.info("Waiting for messages...")

		try:
			async for msg in consumer:
				log.info("Received message: key=%s, value=%s", msg.key, msg.value)

				event = msg.value
				log.info("Parsed event: %s", event)

				# Реагируем только на события добавления трека
				if event.get("event_type") == "track.added":
					payload = event.get("payload", {})
					track_id = str(payload.get("spotify_track_id"))
					log.info("Processing track.added event for track_id=%s", track_id)

					try:
						# 1. Запрашиваем метаданные из Catalog Service через gRPC
						stub = get_catalog_stub()
						request = catalog_pb2.GetTrackRequest(track_id=track_id)
						response = await stub.GetTrack(request)

						if response.found:
							title = response.track.title
							artist = response.track.artist
							cover = response.track.cover
							log.info("Got metadata from catalog: title=%s, artist=%s", title, artist)
						else:
							title = "Неизвестный трек"
							artist = "Неизвестный исполнитель"
							cover = ""
							log.warning("Track %s not found in catalog", track_id)

						# 2. Обновляем локальную БД
						async with async_session_factory() as db:
							stmt = select(PlaylistTrack).where(
								PlaylistTrack.spotify_track_id == track_id
							)
							res = await db.execute(stmt)
							tracks_to_update = res.scalars().all()

							log.info("Found %d tracks in DB for track_id=%s", len(tracks_to_update), track_id)

							for track in tracks_to_update:
								log.info(
									"Updating track: id=%d, old_title=%s, new_title=%s",
									track.id, track.title, title
								)
								track.title = title
								track.artist = artist
								track.cover = cover

							if tracks_to_update:
								await db.commit()
								log.info(
									"Enriched metadata for track_id=%s (%d occurrences)",
									track_id, len(tracks_to_update)
								)
							else:
								log.warning("No tracks found in DB for track_id=%s", track_id)
					except Exception as e:
						log.error("Failed to enrich track %s: %s", track_id, e, exc_info=True)
				else:
					log.info("Skipping event type: %s", event.get('event_type'))
		finally:
			await consumer.stop()
			log.info("Consumer stopped")
	except Exception as e:
		log.error("Fatal error in enrichment consumer: %s", e, exc_info=True)
		raise