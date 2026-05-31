# shared/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+asyncpg://music:music@postgres:5432/music"
    sync_database_url: str = "postgresql://music:music@postgres:5432/music"
    redis_url: str = "redis://redis:6379/0"
    kafka_bootstrap_servers: str = "kafka:9092"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_ttl_seconds: int = 900
    refresh_token_ttl_seconds: int = 604800
    user_grpc_host: str = "user-service"
    user_grpc_port: int = 50051
    playlist_grpc_host: str = "playlist-service"
    playlist_grpc_port: int = 50052
    spotify_api_base_url: str = "https://api.spotify.com/v1"
    spotify_bearer_token: str = ""

@lru_cache
def get_settings() -> Settings:
    return Settings()
