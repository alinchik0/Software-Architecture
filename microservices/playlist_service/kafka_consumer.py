import asyncio
import json
import logging
import grpc
import sys
import os

# Добавляем корень проекта в путь для импорта shared и catalog_service
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from aiokafka import AIOKafkaConsumer
from sqlalchemy import select

from shared.database import async_session_factory
from shared.models.playlist import PlaylistTrack
from catalog_service import catalog_pb2, catalog_pb2_grpc
from playlist_service.config import settings

log = logging.getLogger("playlist-service.consumer")

# Глобальные переменные для gRPC клиента (ленивая инициализация)
_catalog_channel = None
_catalog_stub = None


def get_catalog_stub():
	global _catalog_channel, _catalog_stub
	if _catalog_channel is None:
		log.info("Enrichment Consumer: Connecting to catalog-service:50053...")
		_catalog_channel = grpc.aio.insecure_channel('catalog-service:50053')
		_catalog_stub = catalog_pb2_grpc.CatalogServiceStub(_catalog_channel)
	return _catalog_stub


async def enrichment_consumer_task():
	"""
	Фоновая задача: слушает Kafka и асинхронно обогащает метаданные треков.
	"""
	consumer = AIOKafkaConsumer(
		settings.KAFKA_TOPIC,
		bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
		group_id='playlist-enrichment-group',
		auto_offset_reset='earliest',
		value_deserializer=lambda v: json.loads(v.decode('utf-8'))
	)

	await consumer.start()
	log.info(f"✅ Enrichment Consumer started, listening to topic: {settings.KAFKA_TOPIC}")

	try:
		async for msg in consumer:
			event = msg.value
			# Реагируем только на события добавления трека
			if event.get("event_type") == "track.added":
				track_id = str(event.get("spotify_track_id"))

				try:
					# 1. Запрашиваем метаданные из Catalog Service через gRPC
					stub = get_catalog_stub()
					request = catalog_pb2.GetTrackRequest(track_id=track_id)
					response = await stub.GetTrack(request)

					if response.found:
						title = response.track.title
						artist = response.track.artist
						cover = response.track.cover
					else:
						title = "Неизвестный трек"
						artist = "Неизвестный исполнитель"
						cover = ""

					# 2. Обновляем локальную БД (меняем заглушки на реальные данные)
					async with async_session_factory() as db:
						stmt = select(PlaylistTrack).where(
							PlaylistTrack.spotify_track_id == track_id,
							PlaylistTrack.title == "Загрузка..."
						)
						res = await db.execute(stmt)
						tracks_to_update = res.scalars().all()

						for track in tracks_to_update:
							track.title = title
							track.artist = artist
							track.cover = cover

						if tracks_to_update:
							await db.commit()
							log.info(f"🔄 Enriched metadata for track: {track_id} ({len(tracks_to_update)} occurrences)")
				except Exception as e:
					log.error(f"Failed to enrich track {track_id}: {e}")
	finally:
		await consumer.stop()