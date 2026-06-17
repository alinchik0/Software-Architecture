from pydantic import BaseModel, Field
from typing import Optional, List


class PlaylistCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = ""
    is_public: bool = False


class PlaylistUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_public: Optional[bool] = None


class TrackAdd(BaseModel):
    spotify_track_id: str = Field(..., min_length=1)
    position: int = 0


class TrackInfo(BaseModel):
    spotify_track_id: str
    position: int
    title: Optional[str] = None
    artist: Optional[str] = None


class PlaylistResponse(BaseModel):
    playlist_id: int
    owner_id: int
    title: str
    description: Optional[str] = ""
    is_public: bool
    tracks: List[TrackInfo] = []


class MessageResponse(BaseModel):
    success: bool
    message: str