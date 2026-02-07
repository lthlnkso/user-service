from collections.abc import Generator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import app.api.routes_auth as routes_auth
import app.services.auth as auth_service
from app.db.base import Base
from app.db.session import get_db
from app.main import app


@pytest.fixture()
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture()
async def client(tmp_path) -> Generator[AsyncClient, None, None]:
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)

    async def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    def _fast_hash(password: str) -> str:
        return f"test-hash::{password}"

    def _fast_verify(plain_password: str, password_hash: str) -> bool:
        return password_hash == _fast_hash(plain_password)

    auth_service.hash_password = _fast_hash
    auth_service.verify_password = _fast_verify
    routes_auth.hash_password = _fast_hash
    routes_auth.verify_password = _fast_verify

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
