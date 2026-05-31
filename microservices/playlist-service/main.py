# playlist-service/main.py
import asyncio
import json
import logging
from concurrent import futures
from fastapi import FastAPI
from redis.asyncio import Redis
from shared.config import get_settings
from shared.db import SessionLocal
from shared.events import KafkaProducer
from shared.grpc_compile import compile_protos
from schemas import PlaylistCreate, PlaylistUpdate, TrackAdd
from services import PlaylistServiceLogic, ServiceError, playlist_to_dict, track_to_dict

compile_protos()
import grpc
import playlist_pb2
import playlist_pb2_grpc

logging.basicConfig(level=logging.INFO, format='{"level":"%(levelname)s","message":"%(message)s"}')
app = FastAPI(title="playlist-service")

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

def track_reply(track) -> playlist_pb2.TrackReply:
    return playlist_pb2.TrackReply(playlist_id=str(track.playlist_id), spotify_track_id=track.spotify_track_id, position=track.position, added_at=str(track.added_at), metadata_json="{}")

def playlist_reply(playlist) -> playlist_pb2.PlaylistReply:
    return playlist_pb2.PlaylistReply(id=str(playlist.id), owner_id=str(playlist.owner_id), title=playlist.title, description=playlist.description or "", is_public=playlist.is_public, created_at=str(playlist.created_at), updated_at=str(playlist.updated_at), tracks=[track_reply(t) for t in playlist.tracks])

class PlaylistGrpc(playlist_pb2_grpc.PlaylistServiceServicer):
    async def _cache(self):
        return Redis.from_url(get_settings().redis_url, decode_responses=True)

    async def CreatePlaylist(self, request, context):
        async with SessionLocal() as session:
            try:
                p = await PlaylistServiceLogic(session, KafkaProducer(), cache=await self._cache()).create(request.owner_id, PlaylistCreate(title=request.title, description=request.description or None, is_public=request.is_public))
                return playlist_reply(p)
            except ServiceError as exc:
                await context.abort(exc.code, exc.message)

    async def GetPlaylist(self, request, context):
        async with SessionLocal() as session:
            try:
                p = await PlaylistServiceLogic(session, cache=await self._cache()).get(request.playlist_id, request.requester_id)
                return playlist_reply(p)
            except ServiceError as exc:
                await context.abort(exc.code, exc.message)

    async def UpdatePlaylist(self, request, context):
        async with SessionLocal() as session:
            try:
                is_public = None if request.is_public == "" else request.is_public.lower() == "true"
                p = await PlaylistServiceLogic(session, KafkaProducer(), cache=await self._cache()).update(request.playlist_id, request.requester_id, PlaylistUpdate(title=request.title or None, description=request.description or None, is_public=is_public))
                return playlist_reply(p)
            except ServiceError as exc:
                await context.abort(exc.code, exc.message)

    async def DeletePlaylist(self, request, context):
        async with SessionLocal() as session:
            try:
                await PlaylistServiceLogic(session, KafkaProducer(), cache=await self._cache()).delete(request.playlist_id, request.requester_id)
                return playlist_pb2.Empty()
            except ServiceError as exc:
                await context.abort(exc.code, exc.message)

    async def AddTrack(self, request, context):
        async with SessionLocal() as session:
            try:
                t = await PlaylistServiceLogic(session, KafkaProducer(), cache=await self._cache()).add_track(request.playlist_id, request.requester_id, TrackAdd(spotify_track_id=request.spotify_track_id, position=request.position))
                return track_reply(t)
            except ServiceError as exc:
                await context.abort(exc.code, exc.message)

    async def RemoveTrack(self, request, context):
        async with SessionLocal() as session:
            try:
                await PlaylistServiceLogic(session, KafkaProducer(), cache=await self._cache()).remove_track(request.playlist_id, request.requester_id, request.spotify_track_id)
                return playlist_pb2.Empty()
            except ServiceError as exc:
                await context.abort(exc.code, exc.message)

    async def ListUserPlaylists(self, request, context):
        async with SessionLocal() as session:
            try:
                items = await PlaylistServiceLogic(session).list_user(request.user_id, request.requester_id, request.visibility or "public")
                return playlist_pb2.PlaylistListReply(playlists=[playlist_reply(p) for p in items])
            except ServiceError as exc:
                await context.abort(exc.code, exc.message)

async def serve_grpc() -> None:
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    playlist_pb2_grpc.add_PlaylistServiceServicer_to_server(PlaylistGrpc(), server)
    server.add_insecure_port("[::]:50052")
    await server.start()
    await server.wait_for_termination()

async def main() -> None:
    import uvicorn
    grpc_task = asyncio.create_task(serve_grpc())
    server = uvicorn.Server(uvicorn.Config(app, host="0.0.0.0", port=8002, log_level="info"))
    await server.serve()
    grpc_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
