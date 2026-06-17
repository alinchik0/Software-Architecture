# playlist-service/config.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.config import SharedSettings

class PlaylistServiceSettings(SharedSettings):
    GRPC_PORT: int = 50052
    KAFKA_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC: str = "user.events"