# user-service

## Auth endpoints

- `POST /users/register` — create user (password is stored hashed).
- `POST /users/login` — get JWT access token.
- `GET /users/me` — get current user by Bearer token.

### JWT settings (optional env vars)

- `JWT_SECRET_KEY` (default: `your-secret-key`)
- `JWT_ALGORITHM` (default: `HS256`)
- `JWT_EXPIRE_MINUTES` (default: `60`)
