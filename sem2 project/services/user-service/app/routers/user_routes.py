from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from typing import List

from app.models.user_model import UserCreate, UserUpdate, UserResponse
from app.models.auth_model import LoginRequest, TokenResponse, AuthenticatedUser
from app.controllers.user_controller import (
    register_user,
    list_users,
    retrieve_user,
    edit_user,
    follow,
    unfollow
)
from app.controllers.auth_controller import login_user, get_authenticated_user
from app.data.database import SessionLocal

router = APIRouter(prefix="/users", tags=["Users"])
security = HTTPBearer()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    new_user = register_user(db, user)
    if not new_user:
        raise HTTPException(status_code=400, detail="Username exists")
    return new_user


@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    token = login_user(db, credentials.username, credentials.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return token


@router.get("/me", response_model=AuthenticatedUser)
def me(
    auth: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    user = get_authenticated_user(db, auth.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token user")
    return {"id": user.id, "username": user.username}


@router.get("/", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db)):
    return list_users(db)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = retrieve_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    updated = edit_user(db, user_id, user)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated


@router.post("/{user_id}/follow/{target_id}")
def follow_user_endpoint(user_id: int, target_id: int, db: Session = Depends(get_db)):
    result = follow(db, user_id, target_id)

    if result is None:
        raise HTTPException(status_code=404, detail="User not found")

    if result == "cannot_follow_self":
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    return result


@router.post("/{user_id}/unfollow/{target_id}")
def unfollow_user_endpoint(user_id: int, target_id: int, db: Session = Depends(get_db)):
    result = unfollow(db, user_id, target_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Follow not found")

    return result
