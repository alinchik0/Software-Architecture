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
        # ВАЖНО: в Kubernetes используем имя сервиса 'catalog-service', а не localhost
        if self._channel is None:
            logger.info("Initializing gRPC channel to Catalog Service at catalog-service:50053...")
            self._channel = grpc.aio.insecure_channel('catalog-service:50053')
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