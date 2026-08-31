from fastapi import APIRouter, Request, Response
import httpx

router = APIRouter()

USER_SERVICE_URL = "http://user-service:8000"
POST_SERVICE_URL = "http://post-service:8000"
NOTIFICATION_SERVICE_URL = "http://notification-service:8000"


async def proxy_request(request: Request, base_url: str, path: str):
    async with httpx.AsyncClient() as client:
        url = f"{base_url}/{path}"

        headers = dict(request.headers)

        # прокидываем user_id если есть
        if hasattr(request.state, "user"):
            token_user_id = request.state.user.get("sub")
            if token_user_id is not None:
                headers["x-user-id"] = str(token_user_id)

        response = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=await request.body()
        )

        excluded_headers = {"content-length", "transfer-encoding", "connection"}
        response_headers = {
            key: value
            for key, value in response.headers.items()
            if key.lower() not in excluded_headers
        }
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=response_headers,
            media_type=response.headers.get("content-type")
        )


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
