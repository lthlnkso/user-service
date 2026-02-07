# user-service

A standalone FastAPI user service for reusable username/password auth.

## Features

- Username + password registration/login
- Password hashing with bcrypt
- JWT access + refresh tokens
- Optional user profile fields (`email`, `full_name`, `avatar_url`, `extra`)
- Simple SQLite default (override with `DATABASE_URL`)

## Quick start

```bash
cd user-service
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload
```

Open docs: `http://127.0.0.1:8000/docs`

## Endpoints

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `GET /users/me`
- `PATCH /users/me`
- `GET /health`

## Notes

- Change `JWT_SECRET_KEY` before production.
- For multi-app deployment, point each client app at this API and validate tokens in downstream services if needed.
