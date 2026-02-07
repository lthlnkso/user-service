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
