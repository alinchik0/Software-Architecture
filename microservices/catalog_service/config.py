from pydantic_settings import BaseSettings


class CatalogServiceSettings(BaseSettings):
	# gRPC порт для этого сервиса
	GRPC_PORT: int = 50053

	# Spotify API
	SPOTIFY_CLIENT_ID: str
	SPOTIFY_CLIENT_SECRET: str

	class Config:
		env_file = ".env"


settings = CatalogServiceSettings()