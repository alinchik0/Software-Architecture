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
        # Порт 50053 - это порт catalog_service
        self.channel = grpc.insecure_channel('localhost:50053')
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
        response = client.search_tracks(q, limit)
        return {
            "tracks": [
                {
                    "id": track.id,
                    "title": track.title,
                    "artist": track.artist,
                    "album": track.album,
                    "genre": track.genre
                }
                for track in response.tracks
            ]
        }
    except grpc.RpcError as e:
        return {"tracks": [], "error": f"gRPC error: {e.details()}"}
    finally:
        client.close()