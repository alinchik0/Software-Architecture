import grpc
from concurrent import futures
import logging
import sys
import os

import httpx

# Добавляем корень проекта в путь для импорта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from catalog_service import catalog_pb2, catalog_pb2_grpc
from catalog_service.spotify_client import spotify_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  # <-- ДОБАВИТЬ ЭТУ СТРОКУ


class CatalogServicer(catalog_pb2_grpc.CatalogServiceServicer):
	# async def GetTrack(self, request, context):
	# 	track_data = await spotify_client.get_track(request.track_id)
	# 	if not track_data:
	# 		return catalog_pb2.GetTrackResponse(found=False)
	#
	# 	return catalog_pb2.GetTrackResponse(
	# 		found=True,
	# 		track=catalog_pb2.Track(
	# 			id=track_data["id"],
	# 			title=track_data["title"],
	# 			artist=track_data["artist"],
	# 			album=track_data["album"],
	# 			genre=track_data.get("genre", "Unknown"),
	# 			cover=track_data.get("cover") or "",
	# 			preview=track_data.get("preview") or ""
	# 		)
	# 	)

	async def GetTrack(self, request, context):
		track_id = request.track_id
		# logger.info(f"Getting track info for ID: {track_id}")

		try:
			# Делаем запрос к Jamendo по конкретному ID
			url = f"https://api.jamendo.com/v3.0/tracks/?client_id={os.getenv('JAMENDO_CLIENT_ID')}&format=json&id={track_id}&audioformat=mp32"
			async with httpx.AsyncClient() as client:
				resp = await client.get(url)
				data = resp.json()

			# Проверяем, что Jamendo вернул результаты
			if data.get("results") and len(data["results"]) > 0:
				item = data["results"][0]

				# ВАЖНО: поле 'audio' из Jamendo маппим в поле 'preview' прото-сообщения
				return catalog_pb2.GetTrackResponse(
					found=True,
					track=catalog_pb2.Track(
						id=str(item["id"]),
						title=item.get("name", "Unknown"),
						artist=item.get("artist_name", "Unknown"),
						album=item.get("album_name", "Unknown"),
						genre=item.get("musicinfo", {}).get("genre", "Unknown") if item.get("musicinfo") else "Unknown",
						cover=item.get("image", ""),
						preview=item.get("audio", "")  # <-- ЭТО КЛЮЧЕВАЯ СТРОКА
					)
				)
			else:
				# logger.warning(f"Track {track_id} not found in Jamendo")
				return catalog_pb2.GetTrackResponse(found=False)

		except Exception as e:
			# logger.error(f"Error fetching track {track_id}: {e}")
			context.set_code(grpc.StatusCode.INTERNAL)
			context.set_details(str(e))
			return catalog_pb2.GetTrackResponse(found=False)

	async def SearchTracks(self, request, context):
		tracks_data = await spotify_client.search_tracks(request.query, request.limit)
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