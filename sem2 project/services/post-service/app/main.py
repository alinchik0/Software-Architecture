from fastapi import FastAPI
from app.routers.post_routes import router as post_router
from app.data.init_db import init_db

app = FastAPI(title="Post Service")


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(post_router)


@app.get("/")
def root():
    return {"message": "Post Service is running"}