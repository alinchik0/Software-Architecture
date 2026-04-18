from fastapi import FastAPI
from app.routers.gateway_routes import router as gateway_router

app = FastAPI(title="API Gateway")

app.include_router(gateway_router)

@app.get("/")
def root():
    return {"message": "API Gateway is running"}