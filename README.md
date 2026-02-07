# user-service

A standalone FastAPI user service for reusable username/password auth.

## Features

- Multi-tenant namespace support (`namespace.username` uniqueness)
- Username + password registration/login
- Password hashing with bcrypt
- JWT access + refresh tokens
- Optional user profile fields (`email`, `full_name`, `avatar_url`, `extra`)
- `extra` profile map constrained to `string:string`
- Avatar upload endpoint with size/type validation
- Simple SQLite default (override with `DATABASE_URL`)

## Quick start

```bash
cd user-service
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
alembic upgrade head
uvicorn app.main:app --reload
```

Open docs: `http://127.0.0.1:8000/docs`

## Endpoints

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `GET /users/me`
- `PATCH /users/me`
- `POST /users/me/avatar` (multipart upload)
- `GET /health`

## Example auth payloads

Register:

```json
{
  "namespace": "app-x",
  "username": "y",
  "password": "supersecret123",
  "email": "y@example.com",
  "extra": {
    "role": "admin",
    "timezone": "UTC"
  }
}
```

Login:

```json
{
  "namespace": "app-x",
  "username": "y",
  "password": "supersecret123"
}
```

## Profile pictures

- Current model stores `avatar_url` (URL string), not binary image data.
- Upload route implemented at `POST /users/me/avatar`
- max file size `2 MB` (`AVATAR_MAX_BYTES`)
- allowed mime types `image/jpeg`, `image/png`, `image/webp`
- uploaded files are served from `/uploads/...`
- for production, store objects in S3-compatible storage and keep URL in DB

Example upload:

```bash
curl -X POST http://127.0.0.1:8000/users/me/avatar \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@/path/to/avatar.png"
```

## Migrations

Use Alembic for schema changes:

```bash
alembic upgrade head
```

Create a new migration after model changes:

```bash
alembic revision -m "describe change"
```

## Notes

- Change `JWT_SECRET_KEY` before production.
- For multi-app deployment, point each client app at this API and validate tokens in downstream services if needed.
