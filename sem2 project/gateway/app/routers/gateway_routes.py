from fastapi import APIRouter, Request
import httpx

router = APIRouter()

USER_SERVICE_URL = "http://user-service:8000"
POST_SERVICE_URL = "http://post-service:8000"
NOTIFICATION_SERVICE_URL = "http://notification-service:8000"


async def proxy_request(request: Request, base_url: str, path: str):
    async with httpx.AsyncClient() as client:
        url = f"{base_url}/{path}"

        response = await client.request(
            method=request.method,
            url=url,
            headers=request.headers.raw,
            content=await request.body()
        )

        return response.json()


# ---- USER SERVICE ----
@router.api_route("/users/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_users(request: Request, path: str):
    return await proxy_request(request, USER_SERVICE_URL, f"users/{path}")


# ---- POST SERVICE ----
@router.api_route("/posts/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_posts(request: Request, path: str):
    return await proxy_request(request, POST_SERVICE_URL, f"posts/{path}")


# ---- NOTIFICATION SERVICE ----
@router.api_route("/notifications/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_notifications(request: Request, path: str):
    return await proxy_request(request, NOTIFICATION_SERVICE_URL, f"notifications/{path}")


# health check
@router.get("/health")
def health():
    return {"status": "ok"}