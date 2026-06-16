# api-gateway/routes/users.py
import json
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from auth.jwt import current_user
from grpc_clients.clients import user_stub, playlist_stub
from routes.auth import grpc_error
import grpc
import user_pb2
import playlist_pb2

router = APIRouter(prefix="/api/v1/users", tags=["users"])

class ProfilePatch(BaseModel):
    username: str | None = Field(default=None, min_length=3)
    profile_data: dict | None = None

def profile(r) -> dict:
    return {"id": r.id, "email": r.email, "username": r.username, "profile_data": json.loads(r.profile_data_json or "{}"), "created_at": r.created_at, "updated_at": r.updated_at}

def playlist(r) -> dict:
    return {"id": r.id, "owner_id": r.owner_id, "title": r.title, "description": r.description, "is_public": r.is_public, "created_at": r.created_at, "updated_at": r.updated_at, "tracks": [{"playlist_id": t.playlist_id, "spotify_track_id": t.spotify_track_id, "position": t.position, "added_at": t.added_at} for t in r.tracks]}

@router.get("/me")
async def me(user_id: str = Depends(current_user)):
    try:
        return {"profile": profile(await user_stub().GetProfile(user_pb2.ProfileRequest(user_id=user_id)))}
    except grpc.aio.AioRpcError as exc:
        raise grpc_error(exc)

@router.patch("/me")
async def update_me(body: ProfilePatch, user_id: str = Depends(current_user)):
    try:
        data = json.dumps(body.profile_data) if body.profile_data is not None else ""
        r = await user_stub().UpdateProfile(user_pb2.UpdateProfileRequest(user_id=user_id, username=body.username or "", profile_data_json=data))
        return {"updated_profile": profile(r)}
    except grpc.aio.AioRpcError as exc:
        raise grpc_error(exc)

@router.get("/{user_id}/playlists")
async def user_playlists(user_id: str, visibility: str = "public", requester_id: str = Depends(current_user)):
    try:
        r = await playlist_stub().ListUserPlaylists(playlist_pb2.ListUserPlaylistsRequest(user_id=user_id, requester_id=requester_id, visibility=visibility))
        return [playlist(p) for p in r.playlists]
    except grpc.aio.AioRpcError as exc:
        raise grpc_error(exc)
