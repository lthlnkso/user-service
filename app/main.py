from fastapi import FastAPI

from app.api.routes_auth import router as auth_router
from app.api.routes_users import router as users_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health", tags=["health"])
def healthcheck():
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(users_router)
