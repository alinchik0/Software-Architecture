from sqlalchemy import Column, Integer, String, ForeignKey
from pydantic import BaseModel, Field
from typing import List

from app.data.database import Base


# ---- DB MODELS ----

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer)
    content = Column(String)


class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    post_id = Column(Integer, ForeignKey("posts.id"))


# ---- API MODELS ----

class PostCreate(BaseModel):
    author_id: int
    content: str = Field(..., min_length=1, max_length=500)


class PostResponse(BaseModel):
    id: int
    author_id: int
    content: str
    likes: List[int]

    class Config:
        from_attributes = True