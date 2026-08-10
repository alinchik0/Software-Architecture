import os
from shared.config import SharedSettings


class GatewaySettings(SharedSettings):
	APP_PORT: int = 8000

	# Pydantic автоматически подхватит эти переменные из docker-compose environment
	USER_GRPC_URL: str = "localhost:50051"
	PLAYLIST_GRPC_URL: str = "localhost:50052"
	CATALOG_GRPC_URL: str = "localhost:50053"