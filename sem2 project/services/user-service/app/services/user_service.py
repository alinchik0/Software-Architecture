from sqlalchemy.orm import Session
from app.models.user_model import User, Follow
from app.core.security import hash_password


def create_user(db: Session, user_data):
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        return None

    user = User(
        username=user_data.username,
        password=hash_password(user_data.password),
        bio=user_data.bio
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return serialize_user(db, user)


def get_all_users(db: Session):
    users = db.query(User).all()
    return [serialize_user(db, u) for u in users]


def get_user_by_id(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    return serialize_user(db, user)


def update_user(db: Session, user_id: int, user_data):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    if user_data.username:
        user.username = user_data.username

    if user_data.bio:
        user.bio = user_data.bio

    db.commit()
    db.refresh(user)

    return serialize_user(db, user)


def follow_user(db: Session, user_id: int, target_id: int):
    if user_id == target_id:
        return "cannot_follow_self"

    user = db.query(User).filter(User.id == user_id).first()
    target = db.query(User).filter(User.id == target_id).first()

    if not user or not target:
        return None

    existing = db.query(Follow).filter(
        Follow.follower_id == user_id,
        Follow.following_id == target_id
    ).first()

    if not existing:
        follow = Follow(follower_id=user_id, following_id=target_id)
        db.add(follow)
        db.commit()

    return {"message": f"{user_id} follows {target_id}"}


def unfollow_user(db: Session, user_id: int, target_id: int):
    follow = db.query(Follow).filter(
        Follow.follower_id == user_id,
        Follow.following_id == target_id
    ).first()

    if not follow:
        return None

    db.delete(follow)
    db.commit()

    return {"message": f"{user_id} unfollowed {target_id}"}


# ---- helpers ----

def serialize_user(db: Session, user: User):
    followers = db.query(Follow).filter(Follow.following_id == user.id).all()
    following = db.query(Follow).filter(Follow.follower_id == user.id).all()

    return {
        "id": user.id,
        "username": user.username,
        "bio": user.bio,
        "followers": [f.follower_id for f in followers],
        "following": [f.following_id for f in following],
    }
