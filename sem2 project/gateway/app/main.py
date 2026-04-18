from fastapi import FastAPI
from app.routers.gateway_routes import router as gateway_router
from app.middleware.auth_middleware import auth_middleware

app = FastAPI(title="API Gateway")

app.middleware("http")(auth_middleware)

app.include_router(gateway_router)

@app.get("/")
def root():
    return {"message": "API Gateway is running"}