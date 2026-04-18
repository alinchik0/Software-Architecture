from sqlalchemy import Column, Integer, String, ForeignKey
from pydantic import BaseModel, Field
from typing import List, Optional

from app.data.database import Base


# ---- DB MODELS ----

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    bio = Column(String)


class Follow(Base):
    __tablename__ = "follows"

    id = Column(Integer, primary_key=True)
    follower_id = Column(Integer, ForeignKey("users.id"))
    following_id = Column(Integer, ForeignKey("users.id"))


# ---- API MODELS ----

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=6)
    bio: Optional[str] = ""


class UserUpdate(BaseModel):
    username: Optional[str] = None
    bio: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    bio: str
    followers: List[int]
    following: List[int]

    class Config:
        from_attributes = True