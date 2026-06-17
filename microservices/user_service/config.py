# user_service/config.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.config import SharedSettings

class UserServiceSettings(SharedSettings):
    GRPC_PORT: int = 50051