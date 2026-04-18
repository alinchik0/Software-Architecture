from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    decode_access_token,
    verify_password,
)
from app.models.user_model import User


def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None

    if not verify_password(password, user.password):
        return None

    return user


def issue_access_token(user: User) -> str:
    return create_access_token({"sub": str(user.id), "username": user.username})


def get_user_from_token(db: Session, token: str):
    payload = decode_access_token(token)
    user_id = payload.get("sub")

    if not user_id:
        return None

    return db.query(User).filter(User.id == int(user_id)).first()
