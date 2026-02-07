# User Service Integration Guide (For Agents)

This guide is for integrating `user-service` into a new website/app.

Goal: plug in authentication and user profile support quickly, isolated by namespace.

## 1) Integration Model

- Shared auth backend: `https://users.lthlnkso.com`
- Per-app tenant isolation via `namespace`
- Unique identity key: `(namespace, username)`

Your app should pick one namespace and always use it for register/login calls.

## 2) One-Time App Setup

1. Pick a namespace slug, for example: `my-new-site`.
2. Create namespace once:

```bash
curl -X POST https://users.lthlnkso.com/userspaces \
  -H "Content-Type: application/json" \
  -d '{"namespace":"my-new-site","name":"My New Site","description":"Auth tenant"}'
```

3. Store this namespace in your app config, for example:
- frontend env: `PUBLIC_USER_NAMESPACE=my-new-site`
- backend env: `USER_NAMESPACE=my-new-site`

## 3) Core Endpoints You Will Use

Base URL: `https://users.lthlnkso.com`

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `POST /auth/change-password`
- `GET /users/me`
- `PATCH /users/me`
- `POST /users/me/avatar`
- `DELETE /users/me/avatar`

## 4) Recommended Auth Flow

1. Register/login with `namespace`, `username`, `password`
2. Save `access_token` + `refresh_token`
3. Send `Authorization: Bearer <access_token>` for protected routes
4. On `401` from protected route, call `/auth/refresh`
5. Replace both tokens with refreshed pair
6. If refresh fails, clear tokens and force login

## 5) Request Examples

Register:

```json
{
  "namespace": "my-new-site",
  "username": "alice",
  "password": "supersecret123",
  "email": "alice@example.com"
}
```

Login:

```json
{
  "namespace": "my-new-site",
  "username": "alice",
  "password": "supersecret123"
}
```

Refresh:

```json
{
  "refresh_token": "<refresh_token>"
}
```

## 6) Frontend Fetch Pattern (Minimal)

```javascript
const USER_API = "https://users.lthlnkso.com";
const NS = "my-new-site";

export async function login(username, password) {
  const res = await fetch(`${USER_API}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ namespace: NS, username, password }),
  });
  if (!res.ok) throw new Error("Login failed");
  return res.json(); // { access_token, refresh_token, token_type }
}

export async function getMe(accessToken) {
  const res = await fetch(`${USER_API}/users/me`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  return res;
}
```

## 7) Token Storage Guidance

- Better security: keep tokens in your backend session/httpOnly cookies.
- Faster integration: store tokens client-side, but understand XSS risk.
- If client-side:
  - keep access token short-lived in memory when possible
  - rotate via refresh flow

## 8) User Profile + Avatar

- Profile update: `PATCH /users/me`
- Avatar upload: `POST /users/me/avatar` multipart `file`
- Avatar remove: `DELETE /users/me/avatar`
- Supported image types: JPEG, PNG, WEBP
- Max avatar size controlled by server (`AVATAR_MAX_BYTES`, currently 1MB default)

## 9) Error Semantics to Handle

- `400`: validation/business rule (duplicate username/email, invalid image, etc.)
- `401`: token/auth problem (invalid/expired/stale token, bad credentials)
- `404`: unknown namespace during registration

## 10) Production Checklist for New App

1. Namespace created once and stored in config
2. Login/register UI wired to user-service
3. Token refresh path implemented
4. Logout clears local auth state
5. Protected views call `/users/me` to hydrate session user
6. App handles 401 globally and redirects to login
7. Smoke-check deployed integration:

```bash
RUN_PROD_TESTS=1 PROD_BASE_URL=https://users.lthlnkso.com \
  /home/lthlnkso/users/user-service/.venv/bin/pytest -q \
  /home/lthlnkso/users/user-service/tests_prod/test_prod_smoke.py
```

## 11) Notes

- Email is optional today; password reset-by-email is not implemented yet.
- This service is namespace-based multi-tenant auth; do not reuse namespace names across unrelated apps.
