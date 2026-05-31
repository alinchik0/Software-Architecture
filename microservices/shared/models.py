# shared/models.py
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    profile_data: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    playlists: Mapped[list["Playlist"]] = relationship(back_populates="owner", cascade="all, delete-orphan")

class Playlist(Base):
    __tablename__ = "playlists"
    __table_args__ = (Index("ix_playlists_owner_public", "owner_id", "is_public"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    owner: Mapped[User] = relationship(back_populates="playlists")
    tracks: Mapped[list["PlaylistTrack"]] = relationship(back_populates="playlist", cascade="all, delete-orphan", lazy="selectin")

class PlaylistTrack(Base):
    __tablename__ = "playlist_tracks"
    playlist_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("playlists.id", ondelete="CASCADE"), primary_key=True, index=True)
    spotify_track_id: Mapped[str] = mapped_column(String, primary_key=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    added_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    playlist: Mapped[Playlist] = relationship(back_populates="tracks")

class KafkaEvent(Base):
    __tablename__ = "kafka_events"
    __table_args__ = (UniqueConstraint("topic", "event_id", name="uq_kafka_events_topic_event_id"),)
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    topic: Mapped[str] = mapped_column(String)
    processed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
