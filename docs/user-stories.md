# User Stories

## US-001 Create a userspace
As an app owner, I can create a userspace namespace so usernames are isolated per app.
Acceptance:
- `POST /userspaces` with unique namespace returns `201`.

## US-002 Create a new user in a userspace
As a user, I can register in an existing userspace.
Acceptance:
- `POST /auth/register` returns access and refresh tokens.

## US-003 Login
As a user, I can login with namespace, username, and password.
Acceptance:
- `POST /auth/login` returns access and refresh tokens.

## US-004 Verify logged-in token for gated activity
As a logged-in user, I can access gated routes with a valid access token.
Acceptance:
- `GET /users/me` with bearer token returns `200`.

## US-005 Logout
As a logged-in user, I can log out and invalidate current tokens.
Acceptance:
- `POST /auth/logout` returns `204`.

## US-006 Verify logged-out token is invalid
As a logged-out user, my old access token can no longer access gated routes.
Acceptance:
- `GET /users/me` with old token returns `401`.

## US-007 Reject bad password
As a user, auth fails with wrong password.
Acceptance:
- `POST /auth/login` with wrong password returns `401`.

## US-008 Reject unknown username
As a user, auth fails for unrecognized username.
Acceptance:
- `POST /auth/login` with unknown username returns `401`.

## US-009 Change password
As a logged-in user, I can change my password.
Acceptance:
- `POST /auth/change-password` with correct current password returns `204`.

## US-010 Old password no longer works after password change
As a user, old password must fail after change.
Acceptance:
- `POST /auth/login` with old password returns `401`.
- `POST /auth/login` with new password returns `200`.

## US-011 Create user avatar
As a user, I can upload an avatar to my profile.
Acceptance:
- `POST /users/me/avatar` with valid image returns `200`.
- response includes a non-null `avatar_url`.

## US-012 Change user avatar
As a user, I can replace my existing avatar.
Acceptance:
- uploading a second avatar returns `200`.
- `avatar_url` changes to a new value.
- previous avatar file is deleted.

## US-013 Delete user avatar
As a user, I can remove my avatar from my profile.
Acceptance:
- `DELETE /users/me/avatar` returns `204`.
- `GET /users/me` returns `avatar_url: null`.

## US-014 Reject avatar upload with unsupported mime type
As a user, I get a clear error when uploading a non-image avatar file.
Acceptance:
- `POST /users/me/avatar` with unsupported content type returns `400`.

## US-015 Reject oversized avatar upload
As a user, I get a clear error when avatar exceeds max file size.
Acceptance:
- `POST /users/me/avatar` with file larger than `AVATAR_MAX_BYTES` returns `400`.

## US-016 Reject invalid image payload
As a user, I get a clear error when file claims image type but has invalid bytes.
Acceptance:
- `POST /users/me/avatar` with corrupt image payload returns `400`.

## US-017 Reject registration in nonexistent namespace
As a user, registration fails when target namespace does not exist.
Acceptance:
- `POST /auth/register` with unknown namespace returns `404`.

## US-018 Reject duplicate username in same namespace
As a user, username must remain unique inside a namespace.
Acceptance:
- First registration succeeds.
- Second `POST /auth/register` with same `namespace` and `username` returns `400`.

## US-019 Duplicate username with different password still fails
As a user, changing password value does not bypass username uniqueness rules.
Acceptance:
- `POST /auth/register` with same `namespace` and `username` but different password returns `400`.

## US-020 Reject malformed access token
As a user, malformed bearer tokens are rejected for protected endpoints.
Acceptance:
- `GET /users/me` with malformed token returns `401`.

## US-021 Reject expired access token
As a user, expired access tokens cannot be used for protected endpoints.
Acceptance:
- `GET /users/me` with expired access token returns `401`.

## US-022 Reject refresh token on access-protected route
As a user, refresh tokens cannot be used where access tokens are required.
Acceptance:
- `GET /users/me` with refresh token returns `401`.

## US-023 Reject malformed refresh token
As a user, malformed refresh token is rejected.
Acceptance:
- `POST /auth/refresh` with malformed token returns `401`.

## US-024 Reject expired refresh token
As a user, expired refresh token cannot mint new credentials.
Acceptance:
- `POST /auth/refresh` with expired refresh token returns `401`.

## US-025 Reject refresh token for inactive user
As a user, refresh fails when account is inactive.
Acceptance:
- `POST /auth/refresh` for inactive user returns `401`.

## US-026 Reject access token for inactive user
As a user, protected resource access fails when account is inactive.
Acceptance:
- `GET /users/me` for inactive user returns `401`.
