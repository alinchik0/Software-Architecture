# user-service/schemas.py
from pydantic import BaseModel, Field

class RegisterIn(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)

class LoginIn(BaseModel):
    login: str
    password: str

class ProfileUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=64)
    profile_data: dict | None = None
