from fastapi import FastAPI
from app.routers.user_routes import router as user_router
from app.data.init_db import init_db

app = FastAPI(title="User Service")


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(user_router)


@app.get("/")
def root():
    return {"message": "User Service is running"}