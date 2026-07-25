import grpc
from concurrent import futures
import logging
import sys
import os

# Добавляем корень проекта в путь для импорта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from catalog_service import catalog_pb2, catalog_pb2_grpc
from catalog_service.spotify_client import spotify_client

logging.basicConfig(level=logging.INFO)


class CatalogServicer(catalog_pb2_grpc.CatalogServiceServicer):
	async def GetTrack(self, request, context):
		track_data = await spotify_client.get_track(request.track_id)
		if not track_data:
			return catalog_pb2.GetTrackResponse(found=False)

		return catalog_pb2.GetTrackResponse(
			found=True,
			track=catalog_pb2.Track(
				id=track_data["id"],
				title=track_data["title"],
				artist=track_data["artist"],
				album=track_data["album"],
				genre=track_data["genre"]
			)
		)

	async def SearchTracks(self, request, context):
		tracks_data = await spotify_client.search_tracks(request.query, request.limit)
		tracks = [
			catalog_pb2.Track(
				id=t["id"], title=t["title"], artist=t["artist"],
				album=t["album"], genre=t["genre"]
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