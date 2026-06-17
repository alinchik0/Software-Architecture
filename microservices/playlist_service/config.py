from pydantic_settings import BaseSettings
import os


class PlaylistServiceSettings(BaseSettings):
    GRPC_PORT: int = 50052
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/music_db"
    REDIS_URL: str = "redis://localhost:6379"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC: str = "playlist.events"
    SPOTIFY_CLIENT_ID: str = ""
    SPOTIFY_CLIENT_SECRET: str = ""
    PLAYLIST_CACHE_TTL: int = 600  # 10 минут

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"