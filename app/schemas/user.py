from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    email: str | None = None
    full_name: str | None = None
    avatar_url: str | None = None
    extra: dict | None = None


class UserUpdate(BaseModel):
    email: str | None = None
    full_name: str | None = None
    avatar_url: str | None = None
    extra: dict | None = None


class UserOut(BaseModel):
    id: str
    username: str
    email: str | None
    full_name: str | None
    avatar_url: str | None
    extra: dict | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
