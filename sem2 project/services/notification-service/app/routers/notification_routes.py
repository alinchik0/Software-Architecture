from fastapi import APIRouter, status
from typing import List

from app.models.notification_model import NotificationCreate, NotificationResponse
from app.controllers.notification_controller import (
    send_notification,
    list_notifications,
    retrieve_user_notifications
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create(notification: NotificationCreate):
    return send_notification(notification)


@router.get("/", response_model=List[NotificationResponse])
def get_notifications():
    return list_notifications()


@router.get("/user/{user_id}", response_model=List[NotificationResponse])
def get_user_notifications(user_id: int):
    return retrieve_user_notifications(user_id)