from pydantic import BaseModel


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    namespace: str
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str
