from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.models.post_model import PostCreate, PostResponse
from app.controllers.post_controller import (
    publish_post,
    list_posts,
    retrieve_post,
    remove_post,
    like,
    feed
)
from app.data.database import SessionLocal

router = APIRouter(prefix="/posts", tags=["Posts"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create(post: PostCreate, db: Session = Depends(get_db)):
    return publish_post(db, post)


@router.get("/", response_model=List[PostResponse])
def get_posts(db: Session = Depends(get_db)):
    return list_posts(db)


@router.get("/{post_id}", response_model=PostResponse)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = retrieve_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.delete("/{post_id}")
def delete(post_id: int, db: Session = Depends(get_db)):
    result = remove_post(db, post_id)
    if not result:
        raise HTTPException(status_code=404, detail="Post not found")
    return result


@router.post("/{post_id}/like/{user_id}")
async def like_post_endpoint(post_id: int, user_id: int, db: Session = Depends(get_db)):
    result = await like(db, post_id, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Post not found")
    return result


@router.get("/feed/{user_id}", response_model=List[PostResponse])
def get_feed(user_id: int, db: Session = Depends(get_db)):
    return feed(db, user_id)