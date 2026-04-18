from pymongo import MongoClient

import os

MONGO_URL = os.getenv(
    "MONGO_URL",
    "mongodb://localhost:27017"
)

client = MongoClient(MONGO_URL)

db = client["notifications_db"]
notifications_collection = db["notifications"]