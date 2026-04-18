from app.services.notification_service import (
    create_notification,
    get_all_notifications,
    get_notifications_by_user
)


def send_notification(notification_data):
    return create_notification(notification_data)


def list_notifications():
    return get_all_notifications()


def retrieve_user_notifications(user_id: int):
    return get_notifications_by_user(user_id)