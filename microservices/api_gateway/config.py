# api-gateway/config.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.config import SharedSettings

class GatewaySettings(SharedSettings):
    APP_PORT: int = 8000
    USER_GRPC_URL: str = "localhost:50051"
    PLAYLIST_GRPC_URL: str = "localhost:50052"