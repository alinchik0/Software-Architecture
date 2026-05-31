# playlist-service/schemas.py
from pydantic import BaseModel, Field

class PlaylistCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    is_public: bool = False

class PlaylistUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    is_public: bool | None = None

class TrackAdd(BaseModel):
    spotify_track_id: str = Field(min_length=1, max_length=128)
    position: int = Field(default=0, ge=0)
