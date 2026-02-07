from pathlib import Path

import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.db.session import get_db
from app.main import app
from app.models.user import User
from app.services.security import create_access_token, create_refresh_token


ASSETS_DIR = Path(__file__).parent / "assets"


async def create_userspace(client: AsyncClient, namespace: str = "app-x") -> dict:
    response = await client.post(
        "/userspaces",
        json={"namespace": namespace, "name": "Application X", "description": "Tenant space"},
    )
    assert response.status_code == 201
    return response.json()


async def register_user(
    client: AsyncClient,
    namespace: str = "app-x",
    username: str = "alice",
    password: str = "supersecret123",
) -> dict:
    response = await client.post(
        "/auth/register",
        json={
            "namespace": namespace,
            "username": username,
            "password": password,
            "email": f"{username}@example.com",
            "extra": {"role": "member"},
        },
    )
    assert response.status_code == 200
    return response.json()


async def login_user(
    client: AsyncClient,
    namespace: str = "app-x",
    username: str = "alice",
    password: str = "supersecret123",
):
    return await client.post(
        "/auth/login",
        json={"namespace": namespace, "username": username, "password": password},
    )


def auth_header(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def upload_avatar_file() -> tuple[str, bytes, str]:
    file_name = "avatar.png"
    payload = (ASSETS_DIR / file_name).read_bytes()
    return (file_name, payload, "image/png")


def avatar_disk_path(avatar_url: str) -> Path:
    relative = avatar_url.removeprefix("/uploads/")
    return Path(settings.uploads_dir) / relative


async def set_user_active_flag(user_id: str, is_active: bool) -> None:
    override_get_db = app.dependency_overrides[get_db]
    db_generator = override_get_db()
    db = await db_generator.__anext__()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        assert user is not None
        user.is_active = is_active
        db.add(user)
        db.commit()
    finally:
        await db_generator.aclose()


@pytest.mark.anyio
async def test_us_001_create_userspace(client: AsyncClient):
    response = await client.post(
        "/userspaces",
        json={"namespace": "app-x", "name": "Application X", "description": "Tenant space"},
    )
    assert response.status_code == 201
    assert response.json()["namespace"] == "app-x"


@pytest.mark.anyio
async def test_us_002_create_new_user(client: AsyncClient):
    await create_userspace(client)
    payload = await register_user(client)
    assert payload["access_token"]
    assert payload["refresh_token"]


@pytest.mark.anyio
async def test_us_003_login(client: AsyncClient):
    await create_userspace(client)
    await register_user(client)

    response = await login_user(client)
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]


@pytest.mark.anyio
async def test_us_004_verify_logged_in_token(client: AsyncClient):
    await create_userspace(client)
    tokens = await register_user(client)

    response = await client.get("/users/me", headers=auth_header(tokens["access_token"]))
    assert response.status_code == 200
    assert response.json()["username"] == "alice"


@pytest.mark.anyio
async def test_us_005_logout(client: AsyncClient):
    await create_userspace(client)
    tokens = await register_user(client)

    response = await client.post("/auth/logout", headers=auth_header(tokens["access_token"]))
    assert response.status_code == 204


@pytest.mark.anyio
async def test_us_006_verify_logged_out_token_is_invalid(client: AsyncClient):
    await create_userspace(client)
    tokens = await register_user(client)

    logout = await client.post("/auth/logout", headers=auth_header(tokens["access_token"]))
    assert logout.status_code == 204

    response = await client.get("/users/me", headers=auth_header(tokens["access_token"]))
    assert response.status_code == 401


@pytest.mark.anyio
async def test_us_007_auth_with_bad_password(client: AsyncClient):
    await create_userspace(client)
    await register_user(client)

    response = await login_user(client, password="wrong-password")
    assert response.status_code == 401


@pytest.mark.anyio
async def test_us_008_auth_with_unrecognized_username(client: AsyncClient):
    await create_userspace(client)
    await register_user(client)

    response = await login_user(client, username="nobody")
    assert response.status_code == 401


@pytest.mark.anyio
async def test_us_009_change_password(client: AsyncClient):
    await create_userspace(client)
    tokens = await register_user(client)

    response = await client.post(
        "/auth/change-password",
        headers=auth_header(tokens["access_token"]),
        json={"current_password": "supersecret123", "new_password": "newsecret456"},
    )
    assert response.status_code == 204


@pytest.mark.anyio
async def test_us_010_old_password_no_longer_valid_after_change(client: AsyncClient):
    await create_userspace(client)
    tokens = await register_user(client)

    change_response = await client.post(
        "/auth/change-password",
        headers=auth_header(tokens["access_token"]),
        json={"current_password": "supersecret123", "new_password": "newsecret456"},
    )
    assert change_response.status_code == 204

    old_login = await login_user(client, password="supersecret123")
    assert old_login.status_code == 401

    new_login = await login_user(client, password="newsecret456")
    assert new_login.status_code == 200


@pytest.mark.anyio
async def test_us_011_create_user_with_avatar(client: AsyncClient):
    await create_userspace(client)
    tokens = await register_user(client)

    response = await client.post(
        "/users/me/avatar",
        headers=auth_header(tokens["access_token"]),
        files={"file": upload_avatar_file()},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["avatar_url"]
    assert avatar_disk_path(body["avatar_url"]).exists()


@pytest.mark.anyio
async def test_us_012_change_avatar_replaces_file(client: AsyncClient):
    await create_userspace(client)
    tokens = await register_user(client)

    first = await client.post(
        "/users/me/avatar",
        headers=auth_header(tokens["access_token"]),
        files={"file": upload_avatar_file()},
    )
    assert first.status_code == 200
    first_avatar_url = first.json()["avatar_url"]
    first_avatar_path = avatar_disk_path(first_avatar_url)
    assert first_avatar_path.exists()

    second = await client.post(
        "/users/me/avatar",
        headers=auth_header(tokens["access_token"]),
        files={"file": upload_avatar_file()},
    )
    assert second.status_code == 200
    second_avatar_url = second.json()["avatar_url"]
    second_avatar_path = avatar_disk_path(second_avatar_url)
    assert second_avatar_url != first_avatar_url
    assert second_avatar_path.exists()
    assert not first_avatar_path.exists()


@pytest.mark.anyio
async def test_us_013_delete_avatar(client: AsyncClient):
    await create_userspace(client)
    tokens = await register_user(client)

    upload = await client.post(
        "/users/me/avatar",
        headers=auth_header(tokens["access_token"]),
        files={"file": upload_avatar_file()},
    )
    assert upload.status_code == 200
    avatar_url = upload.json()["avatar_url"]
    avatar_path = avatar_disk_path(avatar_url)
    assert avatar_path.exists()

    delete = await client.delete(
        "/users/me/avatar",
        headers=auth_header(tokens["access_token"]),
    )
    assert delete.status_code == 204
    assert not avatar_path.exists()

    me = await client.get("/users/me", headers=auth_header(tokens["access_token"]))
    assert me.status_code == 200
    assert me.json()["avatar_url"] is None


@pytest.mark.anyio
async def test_us_014_reject_avatar_with_unsupported_mime_type(client: AsyncClient):
    await create_userspace(client)
    tokens = await register_user(client)

    response = await client.post(
        "/users/me/avatar",
        headers=auth_header(tokens["access_token"]),
        files={"file": ("avatar.txt", b"not-an-image", "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported file type. Use JPEG, PNG, or WEBP"


@pytest.mark.anyio
async def test_us_015_reject_avatar_that_exceeds_max_size(client: AsyncClient):
    await create_userspace(client)
    tokens = await register_user(client)

    original_max_bytes = settings.avatar_max_bytes
    settings.avatar_max_bytes = 64
    try:
        too_large_payload = b"a" * (settings.avatar_max_bytes + 1)
        response = await client.post(
            "/users/me/avatar",
            headers=auth_header(tokens["access_token"]),
            files={"file": ("avatar.png", too_large_payload, "image/png")},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == f"File too large. Max size is {settings.avatar_max_bytes} bytes"
    finally:
        settings.avatar_max_bytes = original_max_bytes


@pytest.mark.anyio
async def test_us_016_reject_avatar_with_invalid_image_payload(client: AsyncClient):
    await create_userspace(client)
    tokens = await register_user(client)

    response = await client.post(
        "/users/me/avatar",
        headers=auth_header(tokens["access_token"]),
        files={"file": ("avatar.png", b"this-is-not-a-valid-png", "image/png")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image payload"


@pytest.mark.anyio
async def test_us_017_reject_register_when_namespace_does_not_exist(client: AsyncClient):
    response = await client.post(
        "/auth/register",
        json={
            "namespace": "missing-space",
            "username": "alice",
            "password": "supersecret123",
            "email": "alice@example.com",
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Namespace not found"


@pytest.mark.anyio
async def test_us_018_reject_duplicate_username_in_same_namespace(client: AsyncClient):
    await create_userspace(client)
    await register_user(client, username="alice", password="supersecret123")

    duplicate = await client.post(
        "/auth/register",
        json={
            "namespace": "app-x",
            "username": "alice",
            "password": "anothersecret789",
            "email": "alice-two@example.com",
        },
    )
    assert duplicate.status_code == 400
    assert duplicate.json()["detail"] == "Username already exists in namespace"


@pytest.mark.anyio
async def test_us_019_duplicate_username_with_different_password_still_fails(client: AsyncClient):
    await create_userspace(client)
    await register_user(client, username="bob", password="supersecret123")

    duplicate = await client.post(
        "/auth/register",
        json={
            "namespace": "app-x",
            "username": "bob",
            "password": "different-password-456",
            "email": "bob-2@example.com",
        },
    )
    assert duplicate.status_code == 400
    assert duplicate.json()["detail"] == "Username already exists in namespace"


@pytest.mark.anyio
async def test_us_020_reject_malformed_access_token(client: AsyncClient):
    await create_userspace(client)
    await register_user(client)

    response = await client.get("/users/me", headers=auth_header("not-a-jwt"))
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


@pytest.mark.anyio
async def test_us_021_reject_expired_access_token(client: AsyncClient):
    await create_userspace(client)
    tokens = await register_user(client)
    me = await client.get("/users/me", headers=auth_header(tokens["access_token"]))
    assert me.status_code == 200
    body = me.json()

    original_expiry = settings.access_token_expire_minutes
    settings.access_token_expire_minutes = -1
    try:
        expired_access_token = create_access_token(body["id"], body["token_version"])
    finally:
        settings.access_token_expire_minutes = original_expiry

    response = await client.get("/users/me", headers=auth_header(expired_access_token))
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


@pytest.mark.anyio
async def test_us_022_reject_refresh_token_for_access_protected_route(client: AsyncClient):
    await create_userspace(client)
    tokens = await register_user(client)

    response = await client.get("/users/me", headers=auth_header(tokens["refresh_token"]))
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token type"


@pytest.mark.anyio
async def test_us_023_reject_refresh_when_token_malformed(client: AsyncClient):
    await create_userspace(client)
    await register_user(client)

    response = await client.post("/auth/refresh", json={"refresh_token": "not-a-jwt"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid refresh token"


@pytest.mark.anyio
async def test_us_024_reject_expired_refresh_token(client: AsyncClient):
    await create_userspace(client)
    tokens = await register_user(client)
    me = await client.get("/users/me", headers=auth_header(tokens["access_token"]))
    assert me.status_code == 200
    body = me.json()

    original_expiry = settings.refresh_token_expire_days
    settings.refresh_token_expire_days = -1
    try:
        expired_refresh_token = create_refresh_token(body["id"], body["token_version"])
    finally:
        settings.refresh_token_expire_days = original_expiry

    response = await client.post("/auth/refresh", json={"refresh_token": expired_refresh_token})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid refresh token"


@pytest.mark.anyio
async def test_us_025_reject_refresh_for_inactive_user(client: AsyncClient):
    await create_userspace(client)
    tokens = await register_user(client)
    me = await client.get("/users/me", headers=auth_header(tokens["access_token"]))
    assert me.status_code == 200
    body = me.json()

    await set_user_active_flag(body["id"], False)

    response = await client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 401
    assert response.json()["detail"] == "User not found or inactive"


@pytest.mark.anyio
async def test_us_026_reject_access_for_inactive_user(client: AsyncClient):
    await create_userspace(client)
    tokens = await register_user(client)
    me = await client.get("/users/me", headers=auth_header(tokens["access_token"]))
    assert me.status_code == 200
    body = me.json()

    await set_user_active_flag(body["id"], False)

    response = await client.get("/users/me", headers=auth_header(tokens["access_token"]))
    assert response.status_code == 401
    assert response.json()["detail"] == "User not found or inactive"
