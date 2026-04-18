from app.data.database import notifications_collection


def create_notification(notification_data):
    result = notifications_collection.insert_one({
        "recipient_id": notification_data.recipient_id,
        "type": notification_data.type,
        "message": notification_data.message
    })

    return {
        "id": str(result.inserted_id),
        "recipient_id": notification_data.recipient_id,
        "type": notification_data.type,
        "message": notification_data.message
    }


def get_all_notifications():
    notifications = notifications_collection.find()
    return [serialize(n) for n in notifications]


def get_notifications_by_user(user_id: int):
    notifications = notifications_collection.find({"recipient_id": user_id})
    return [serialize(n) for n in notifications]


def serialize(notification):
    return {
        "id": str(notification["_id"]),
        "recipient_id": notification["recipient_id"],
        "type": notification["type"],
        "message": notification["message"]
    }