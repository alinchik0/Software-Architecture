from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from shared.models.user import Base  # переиспользуем Base из user_service


class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    tracks = relationship("PlaylistTrack", back_populates="playlist", cascade="all, delete-orphan",
                          order_by="PlaylistTrack.position")


# class PlaylistTrack(Base):
#     __tablename__ = "playlist_tracks"
#     __table_args__ = (
#         UniqueConstraint("playlist_id", "spotify_track_id", name="uq_playlist_track"),
#     )
#
#     id = Column(Integer, primary_key=True, index=True)
#     playlist_id = Column(Integer, ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False, index=True)
#     spotify_track_id = Column(String(64), nullable=False, index=True)
#     position = Column(Integer, nullable=False, default=0)
#     added_at = Column(DateTime(timezone=True), server_default=func.now())
#
#     playlist = relationship("Playlist", back_populates="tracks")

class PlaylistTrack(Base):
    __tablename__ = "playlist_tracks"
    __table_args__ = (
        UniqueConstraint("playlist_id", "spotify_track_id", name="uq_playlist_track"),
    )

    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False, index=True)
    spotify_track_id = Column(String(64), nullable=False, index=True)

    # НОВЫЕ ПОЛЯ для асинхронного обогащения (денормализация)
    title = Column(String(255), nullable=True, default="Загрузка...")
    artist = Column(String(255), nullable=True, default="Загрузка...")
    cover = Column(String(512), nullable=True, default="")

    position = Column(Integer, nullable=False, default=0)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    playlist = relationship("Playlist", back_populates="tracks")