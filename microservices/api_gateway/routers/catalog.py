# api_gateway/routers/catalog.py

from fastapi import APIRouter, Query
from typing import List
import grpc
import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from catalog_service import catalog_pb2, catalog_pb2_grpc
from api_gateway.config import GatewaySettings

router = APIRouter(prefix="/catalog", tags=["catalog"])
cfg = GatewaySettings()

class CatalogGRPCClient:
    def __init__(self):
        # Берем адрес из конфига. В Docker это будет 'catalog_service:50053', локально - 'localhost:50053'
        grpc_url = getattr(cfg, 'CATALOG_GRPC_URL', 'localhost:50053')
        self.channel = grpc.insecure_channel(grpc_url)
        self.stub = catalog_pb2_grpc.CatalogServiceStub(self.channel)

    def search_tracks(self, query: str, limit: int = 10):
        request = catalog_pb2.SearchTracksRequest(query=query, limit=limit)
        return self.stub.SearchTracks(request)

    def close(self):
        self.channel.close()

@router.get("/search")
async def search_tracks(q: str = Query(..., description="Search query"), limit: int = Query(10, le=50)):
    """Поиск треков в каталоге Spotify"""
    client = CatalogGRPCClient()
    try:
        request = catalog_pb2.SearchTracksRequest(query=q, limit=limit)
        response = client.stub.SearchTracks(request)

        return {
            "tracks": [
                {
                    "id": track.id,
                    "title": track.title,
                    "artist": track.artist,
                    "album": track.album,
                    "genre": track.genre,
                    "cover": track.cover,  # <-- ДОБАВИЛИ ОБЛОЖКУ
                    "preview": track.preview  # <-- ДОБАВИЛИ ССЫЛКУ НА АУДИО (ЭТО ГЛАВНОЕ!)
                }
                for track in response.tracks
            ]
        }
    except grpc.RpcError as e:
        return {"tracks": [], "error": f"gRPC error: {e.details()}"}
    finally:
        client.close()


from fastapi import Response
from fastapi.responses import StreamingResponse
import httpx


# @router.get("/stream/{track_id}")
# async def stream_track(track_id: str):
#     """Проксирует аудио-поток с Jamendo через наш сервер (обходит CORS)"""
#     # Сначала получаем информацию о треке через gRPC
#     client = CatalogGRPCClient()
#     try:
#         request = catalog_pb2.GetTrackRequest(track_id=track_id)
#         response = client.stub.GetTrack(request)
#
#         if not response.found or not response.track.preview:
#             return Response(status_code=404, content="Track not found or no audio available")
#
#         audio_url = response.track.preview
#
#         # Скачиваем аудио с Jamendo и стримим клиенту
#         async with httpx.AsyncClient() as http_client:
#             async with http_client.stream("GET", audio_url) as resp:
#                 if resp.status_code != 200:
#                     return Response(status_code=502, content="Failed to fetch audio from provider")
#
#                 # Возвращаем поток с правильными заголовками
#                 return StreamingResponse(
#                     resp.aiter_bytes(),
#                     media_type="audio/mpeg",
#                     headers={
#                         "Accept-Ranges": "bytes",
#                         "Cache-Control": "public, max-age=3600"
#                     }
#                 )
#     except Exception as e:
#         return Response(status_code=500, content=f"Streaming error: {str(e)}")
#     finally:
#         client.close()

@router.get("/stream/{track_id}")
async def stream_track(track_id: str):
    """Проксирует аудио-файл с Jamendo через наш сервер"""
    client = CatalogGRPCClient()
    try:
        request = catalog_pb2.GetTrackRequest(track_id=track_id)
        response = client.stub.GetTrack(request)

        if not response.found or not response.track.preview:
            return Response(status_code=404, content="Track not found or no audio available")

        audio_url = response.track.preview

        # Скачиваем файл целиком в память. follow_redirects=True критически важен для Jamendo.
        async with httpx.AsyncClient(timeout=15.0) as http_client:
            resp = await http_client.get(audio_url, follow_redirects=True)

            if resp.status_code != 200:
                return Response(status_code=502, content="Failed to fetch audio from provider")

            # Возвращаем полный файл. Это предотвращает ERR_INCOMPLETE_CHUNKED_ENCODING
            return Response(
                content=resp.content,
                media_type="audio/mpeg",
                headers={
                    "Accept-Ranges": "bytes",
                    "Cache-Control": "public, max-age=3600"
                }
            )
    except Exception as e:
        return Response(status_code=500, content=f"Streaming error: {str(e)}")
    finally:
        client.close()