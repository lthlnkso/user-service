from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes_auth import router as auth_router
from app.api.routes_users import router as users_router
from app.api.routes_userspaces import router as userspaces_router
from app.core.config import settings

app = FastAPI(title=settings.app_name)
app.mount("/uploads", StaticFiles(directory=settings.uploads_dir, check_dir=False), name="uploads")


@app.on_event("startup")
async def startup() -> None:
    Path(settings.uploads_dir).mkdir(parents=True, exist_ok=True)


@app.get("/health", tags=["health"])
async def healthcheck():
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(userspaces_router)
