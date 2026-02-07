import pytest
from httpx import AsyncClient


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
