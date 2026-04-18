from sqlalchemy.orm import Session
from app.models.post_model import Post, Like
import httpx

NOTIFICATION_SERVICE_URL = "http://127.0.0.1:8003"


def create_post(db: Session, post_data):
    post = Post(
        author_id=post_data.author_id,
        content=post_data.content
    )

    db.add(post)
    db.commit()
    db.refresh(post)

    return serialize_post(db, post)


def get_all_posts(db: Session):
    posts = db.query(Post).all()
    return [serialize_post(db, p) for p in posts]


def get_post_by_id(db: Session, post_id: int):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        return None
    return serialize_post(db, post)


def delete_post(db: Session, post_id: int):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        return None

    db.query(Like).filter(Like.post_id == post_id).delete()
    db.delete(post)
    db.commit()

    return {"message": f"Post {post_id} deleted"}


async def like_post(db: Session, post_id: int, user_id: int):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        return None

    existing = db.query(Like).filter(
        Like.post_id == post_id,
        Like.user_id == user_id
    ).first()

    if not existing:
        like = Like(user_id=user_id, post_id=post_id)
        db.add(like)
        db.commit()

        await send_notification(
            recipient_id=post.author_id,
            sender_id=user_id,
            post_id=post_id
        )

    return {"message": f"User {user_id} liked Post {post_id}"}


def get_feed(db: Session, user_id: int):
    posts = db.query(Post).all()
    return [serialize_post(db, p) for p in posts]


# ---- helpers ----

def serialize_post(db: Session, post: Post):
    likes = db.query(Like).filter(Like.post_id == post.id).all()

    return {
        "id": post.id,
        "author_id": post.author_id,
        "content": post.content,
        "likes": [l.user_id for l in likes]
    }


async def send_notification(recipient_id: int, sender_id: int, post_id: int):
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{NOTIFICATION_SERVICE_URL}/notifications/",
            json={
                "recipient_id": recipient_id,
                "type": "like",
                "message": f"User {sender_id} liked your post {post_id}"
            }
        )