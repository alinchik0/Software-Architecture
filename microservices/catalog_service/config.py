# microservices/catalog_service/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict


class CatalogServiceSettings(BaseSettings):
	# Настройки самого Catalog Service
	GRPC_PORT: int = 50053

	# Spotify API
	SPOTIFY_CLIENT_ID: str
	SPOTIFY_CLIENT_SECRET: str

	# Разрешаем игнорировать переменные из .env, которые нужны другим сервисам (БД, Redis, JWT и т.д.)
	model_config = SettingsConfigDict(
		env_file=".env",
		extra="ignore"  # <-- ЭТА СТРОКА РЕШАЕТ ПРОБЛЕМУ
	)


settings = CatalogServiceSettings()