# from pydantic_settings import BaseSettings
# import os
#
#
# class PlaylistServiceSettings(BaseSettings):
#     GRPC_PORT: int = 50052
#     DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/music_db"
#     REDIS_URL: str = "redis://localhost:6379"
#     KAFKA_BOOTSTRAP_SERVERS: str = "kafka:29092"
#     KAFKA_TOPIC: str = "music_events"
#
#     SPOTIFY_CLIENT_ID: str = ""
#     SPOTIFY_CLIENT_SECRET: str = ""
#     PLAYLIST_CACHE_TTL: int = 600  # 10 минут
#
#     class Config:
#         env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
#         env_file_encoding = "utf-8"
#         extra = "ignore"

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class PlaylistServiceSettings(BaseSettings):
    GRPC_PORT: int = 50052
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/music_db"
    REDIS_URL: str = "redis://redis:6379"

    # Единые настройки Kafka (внутри Docker используем имя сервиса 'kafka')
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:29092"
    KAFKA_TOPIC: str = "music_events"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = PlaylistServiceSettings()