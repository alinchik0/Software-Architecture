# import grpc
# import logging
# import sys
# import os
#
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
#
# # Импортируем сгенерированные файлы из catalog_service
# from catalog_service import catalog_pb2, catalog_pb2_grpc
#
# logger = logging.getLogger(__name__)
#
# class CatalogClient:
#     def __init__(self):
#         # Адрес catalog_service (при локальном запуске localhost, в docker - catalog_service)
#         self.channel = grpc.aio.insecure_channel('localhost:50053')
#         self.stub = catalog_pb2_grpc.CatalogServiceStub(self.channel)
#
#     async def get_track_info(self, track_id: str) -> dict | None:
#         try:
#             request = catalog_pb2.GetTrackRequest(track_id=track_id)
#             response = await self.stub.GetTrack(request)
#             if response.found:
#                 return {
#                     "id": response.track.id,
#                     "title": response.track.title,
#                     "artist": response.track.artist,
#                     "album": response.track.album,
#                     "genre": response.track.genre
#                 }
#             return None
#         except grpc.RpcError as e:
#             logger.error(f"gRPC error calling Catalog Service: {e.details()}")
#             return None
#
# # Глобальный экземпляр
# catalog_client = CatalogClient()

# microservices/playlist_service/catalog_client.py

import grpc
import logging
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from catalog_service import catalog_pb2, catalog_pb2_grpc

logger = logging.getLogger(__name__)


class CatalogClient:
    def __init__(self):
        # НЕ создаем канал здесь!
        self._channel = None
        self._stub = None

    def _get_stub(self):
        # Создаем канал и stub лениво, внутри уже запущенного event loop
        if self._channel is None:
            logger.info("Initializing gRPC channel to Catalog Service...")
            self._channel = grpc.aio.insecure_channel('localhost:50053')
            self._stub = catalog_pb2_grpc.CatalogServiceStub(self._channel)
        return self._stub

    async def get_track_info(self, track_id: str) -> dict | None:
        try:
            stub = self._get_stub()  # Получаем stub, привязанный к текущему loop
            request = catalog_pb2.GetTrackRequest(track_id=track_id)
            response = await stub.GetTrack(request)

            if response.found:
                return {
                    "id": response.track.id,
                    "title": response.track.title,
                    "artist": response.track.artist,
                    "album": response.track.album,
                    "genre": response.track.genre
                }
            logger.warning(f"Track {track_id} not found in Catalog Service")
            return None
        except grpc.RpcError as e:
            logger.error(f"gRPC error calling Catalog Service: {e.code()} - {e.details()}")
            return None


# Глобальный экземпляр (теперь он безопасен, так как инициализация отложена)
catalog_client = CatalogClient()