# Gateway Service

## Auth behavior

- JWT verification is performed in gateway middleware.
- Public routes (no token required):
  - `GET /`
  - `GET /health`
  - `POST /users/register`
  - `POST /users/login`
- For protected routes, gateway expects `Authorization: Bearer <token>`.
- Gateway reads JWT config from environment:
  - `JWT_SECRET_KEY`
  - `JWT_ALGORITHM`

## Proxy behavior

- Gateway proxies requests to `user-service`, `post-service`, and `notification-service`.
- If JWT is valid, gateway forwards user id to downstream services via `x-user-id` header (from token claim `sub`).
