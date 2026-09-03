# microservices/catalog_service/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict


class CatalogServiceSettings(BaseSettings):
	GRPC_PORT: int = 50053

	# Jamendo API
	JAMENDO_CLIENT_ID: str

	model_config = SettingsConfigDict(
		env_file=".env",
		extra="ignore"
	)


settings = CatalogServiceSettings()