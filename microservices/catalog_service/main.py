import grpc
from concurrent import futures
import logging
import httpx
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from shared.redis_cache import redis_client
import json

# Добавляем корень проекта в путь для импорта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from catalog_service import catalog_pb2, catalog_pb2_grpc
from catalog_service.spotify_client import spotify_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  # <-- ДОБАВИТЬ ЭТУ СТРОКУ


class CatalogServicer(catalog_pb2_grpc.CatalogServiceServicer):

	# async def GetTrack(self, request, context):
	# 	track_id = request.track_id
	# 	logging.info(f"Getting track info for ID: {track_id}")
	#
	# 	try:
	# 		# Делаем запрос к Jamendo по конкретному ID
	# 		url = f"https://api.jamendo.com/v3.0/tracks/?client_id={os.getenv('JAMENDO_CLIENT_ID')}&format=json&id={track_id}&audioformat=mp32"
	# 		async with httpx.AsyncClient() as client:
	# 			resp = await client.get(url)
	# 			data = resp.json()
	#
	# 		# Проверяем, что Jamendo вернул результаты
	# 		if data.get("results") and len(data["results"]) > 0:
	# 			item = data["results"][0]
	#
	# 			# ВАЖНО: поле 'audio' из Jamendo маппим в поле 'preview' прото-сообщения
	# 			return catalog_pb2.GetTrackResponse(
	# 				found=True,
	# 				track=catalog_pb2.Track(
	# 					id=str(item["id"]),
	# 					title=item.get("name", "Unknown"),
	# 					artist=item.get("artist_name", "Unknown"),
	# 					album=item.get("album_name", "Unknown"),
	# 					genre=item.get("musicinfo", {}).get("genre", "Unknown") if item.get("musicinfo") else "Unknown",
	# 					cover=item.get("image", ""),
	# 					preview=item.get("audio", "")  # <-- ЭТО КЛЮЧЕВАЯ СТРОКА
	# 				)
	# 			)
	# 		else:
	# 			logging.warning(f"Track {track_id} not found in Jamendo")
	# 			return catalog_pb2.GetTrackResponse(found=False)
	#
	# 	except Exception as e:
	# 		logging.error(f"Error fetching track {track_id}: {e}")
	# 		context.set_code(grpc.StatusCode.INTERNAL)
	# 		context.set_details(str(e))
	# 		return catalog_pb2.GetTrackResponse(found=False)

	async def GetTrack(self, request, context):
		track_id = request.track_id

		# 1. Проверяем кэш
		cache_key = f"track:{track_id}"
		try:
			cached = await redis_client.get(cache_key)
			if cached:
				logger.info(f"Cache hit for track: {track_id}")
				track_data = json.loads(cached)
			else:
				# Cache miss — запрашиваем из Jamendo
				logger.info(f"Cache miss for track: {track_id}, fetching from Jamendo")
				track_data = await spotify_client.get_track(track_id)

				if track_data:
					# Сохраняем в кэш на 1 час
					try:
						await redis_client.setex(cache_key, 3600, json.dumps(track_data))
						logger.info(f"Track metadata cached for 3600 seconds: {track_id}")
					except Exception as e:
						logger.warning(f"Redis cache write failed: {e}")
		except Exception as e:
			logger.warning(f"Redis cache read failed: {e}")
			track_data = await spotify_client.get_track(track_id)

		if not track_data:
			return catalog_pb2.GetTrackResponse(found=False)

		return catalog_pb2.GetTrackResponse(
			found=True,
			track=catalog_pb2.Track(
				id=track_data["id"],
				title=track_data["title"],
				artist=track_data["artist"],
				album=track_data["album"],
				genre=track_data.get("genre", "Unknown"),
				cover=track_data.get("cover") or "",
				preview=track_data.get("preview") or ""
			)
		)

	# async def SearchTracks(self, request, context):
	# 	tracks_data = await spotify_client.search_tracks(request.query, request.limit)
	# 	tracks = [
	# 		catalog_pb2.Track(
	# 			id=t["id"], title=t["title"], artist=t["artist"],
	# 			album=t["album"], genre=t.get("genre", "Unknown"),
	# 			cover=t.get("cover") or "", preview=t.get("preview") or ""
	# 		) for t in tracks_data
	# 	]
	# 	return catalog_pb2.SearchTracksResponse(tracks=tracks)


	async def SearchTracks(self, request, context):
		query = request.query
		limit = request.limit

		# 1. Проверяем кэш
		cache_key = f"search:{query}:{limit}"
		try:
			cached = await redis_client.get(cache_key)
			if cached:
				logger.info(f"Cache hit for search: {query}")
				tracks_data = json.loads(cached)
			else:
				# Cache miss — запрашиваем из Jamendo
				logger.info(f"Cache miss for search: {query}, fetching from Jamendo")
				tracks_data = await spotify_client.search_tracks(query, limit)

				# Сохраняем в кэш на 10 минут
				try:
					await redis_client.setex(cache_key, 600, json.dumps(tracks_data))
					logger.info(f"Search results cached for 600 seconds: {query}")
				except Exception as e:
					logger.warning(f"Redis cache write failed: {e}")
		except Exception as e:
			logger.warning(f"Redis cache read failed: {e}")
			tracks_data = await spotify_client.search_tracks(query, limit)

		tracks = [
			catalog_pb2.Track(
				id=t["id"], title=t["title"], artist=t["artist"],
				album=t["album"], genre=t.get("genre", "Unknown"),
				cover=t.get("cover") or "", preview=t.get("preview") or ""
			) for t in tracks_data
		]
		return catalog_pb2.SearchTracksResponse(tracks=tracks)


async def serve():
	server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
	catalog_pb2_grpc.add_CatalogServiceServicer_to_server(CatalogServicer(), server)
	server.add_insecure_port(f'[::]:{50053}')  # Порт из config

	logging.info("Catalog Service (gRPC) started on port 50053")
	await server.start()
	await server.wait_for_termination()


if __name__ == '__main__':
	import asyncio

	asyncio.run(serve())