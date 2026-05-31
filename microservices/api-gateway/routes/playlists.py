# api-gateway/routes/playlists.py
from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, Field
from auth.jwt import current_user
from grpc_clients.clients import playlist_stub
from routes.auth import grpc_error
from routes.users import playlist
import grpc
import playlist_pb2

router = APIRouter(prefix="/api/v1/playlists", tags=["playlists"])

class PlaylistCreateBody(BaseModel):
    title: str = Field(min_length=1)
    description: str | None = None
    is_public: bool = False
class PlaylistPatchBody(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    description: str | None = None
    is_public: bool | None = None
class TrackBody(BaseModel):
    spotify_track_id: str
    position: int = 0

@router.post("")
async def create(body: PlaylistCreateBody, user_id: str = Depends(current_user)):
    try:
        r = await playlist_stub().CreatePlaylist(playlist_pb2.CreatePlaylistRequest(owner_id=user_id, title=body.title, description=body.description or "", is_public=body.is_public))
        return {"playlist": playlist(r)}
    except grpc.aio.AioRpcError as exc:
        raise grpc_error(exc)

@router.get("/{playlist_id}")
async def get(playlist_id: str, user_id: str = Depends(current_user)):
    try:
        return {"playlist": playlist(await playlist_stub().GetPlaylist(playlist_pb2.GetPlaylistRequest(playlist_id=playlist_id, requester_id=user_id)))}
    except grpc.aio.AioRpcError as exc:
        raise grpc_error(exc)

@router.patch("/{playlist_id}")
async def patch(playlist_id: str, body: PlaylistPatchBody, user_id: str = Depends(current_user)):
    try:
        is_public = "" if body.is_public is None else str(body.is_public).lower()
        r = await playlist_stub().UpdatePlaylist(playlist_pb2.UpdatePlaylistRequest(playlist_id=playlist_id, requester_id=user_id, title=body.title or "", description=body.description or "", is_public=is_public))
        return {"updated_playlist": playlist(r)}
    except grpc.aio.AioRpcError as exc:
        raise grpc_error(exc)

@router.delete("/{playlist_id}", status_code=204)
async def delete(playlist_id: str, user_id: str = Depends(current_user)):
    try:
        await playlist_stub().DeletePlaylist(playlist_pb2.DeletePlaylistRequest(playlist_id=playlist_id, requester_id=user_id))
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except grpc.aio.AioRpcError as exc:
        raise grpc_error(exc)

@router.post("/{playlist_id}/tracks")
async def add_track(playlist_id: str, body: TrackBody, user_id: str = Depends(current_user)):
    try:
        t = await playlist_stub().AddTrack(playlist_pb2.AddTrackRequest(playlist_id=playlist_id, requester_id=user_id, spotify_track_id=body.spotify_track_id, position=body.position))
        return {"track_entry": {"playlist_id": t.playlist_id, "spotify_track_id": t.spotify_track_id, "position": t.position, "added_at": t.added_at}}
    except grpc.aio.AioRpcError as exc:
        raise grpc_error(exc)

@router.delete("/{playlist_id}/tracks/{spotify_track_id}", status_code=204)
async def remove_track(playlist_id: str, spotify_track_id: str, user_id: str = Depends(current_user)):
    try:
        await playlist_stub().RemoveTrack(playlist_pb2.RemoveTrackRequest(playlist_id=playlist_id, requester_id=user_id, spotify_track_id=spotify_track_id))
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except grpc.aio.AioRpcError as exc:
        raise grpc_error(exc)
