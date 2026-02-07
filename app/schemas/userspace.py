from pydantic import BaseModel, ConfigDict, Field


class UserSpaceCreate(BaseModel):
    namespace: str = Field(min_length=2, max_length=100)
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=255)


class UserSpaceOut(BaseModel):
    namespace: str
    name: str
    description: str | None

    model_config = ConfigDict(from_attributes=True)
