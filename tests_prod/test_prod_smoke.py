import os

import pytest
import httpx


BASE_URL = os.getenv("PROD_BASE_URL", "https://users.lthlnkso.com").rstrip("/")


@pytest.fixture(scope="session")
def prod_guard() -> None:
    if os.getenv("RUN_PROD_TESTS") != "1":
        pytest.skip("Prod smoke tests are opt-in. Set RUN_PROD_TESTS=1 to run.")


@pytest.fixture(scope="session")
def client(prod_guard: None) -> httpx.Client:
    with httpx.Client(base_url=BASE_URL, timeout=10.0, follow_redirects=True) as c:
        yield c


def test_prod_healthcheck(client: httpx.Client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json().get("status") == "ok"


def test_prod_openapi_has_core_paths(client: httpx.Client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json().get("paths", {})
    for expected in ["/health", "/auth/login", "/auth/register", "/users/me"]:
        assert expected in paths


def test_prod_users_me_requires_bearer_token(client: httpx.Client):
    response = client.get("/users/me")
    assert response.status_code == 401
    assert "detail" in response.json()


def test_prod_refresh_rejects_malformed_token(client: httpx.Client):
    response = client.post("/auth/refresh", json={"refresh_token": "not-a-jwt"})
    assert response.status_code == 401
    assert response.json().get("detail") == "Invalid refresh token"


def test_prod_login_rejects_bad_credentials(client: httpx.Client):
    response = client.post(
        "/auth/login",
        json={
            "namespace": "nonexistent-ns",
            "username": "nonexistent-user",
            "password": "wrong-password",
        },
    )
    assert response.status_code == 401
    assert "detail" in response.json()
