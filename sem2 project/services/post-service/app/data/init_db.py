import time
from sqlalchemy.exc import OperationalError
from app.data.database import engine, Base


def init_db():
    retries = 10

    for i in range(retries):
        try:
            Base.metadata.create_all(bind=engine)
            print("DB connected successfully")
            return
        except OperationalError:
            print(f"DB not ready, retry {i+1}/{retries}...")
            time.sleep(3)

    raise Exception("Database connection failed")