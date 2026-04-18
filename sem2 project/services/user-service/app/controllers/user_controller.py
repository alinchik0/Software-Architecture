from app.services.user_service import (
    create_user,
    get_all_users,
    get_user_by_id,
    update_user,
    follow_user,
    unfollow_user
)


def register_user(db, user_data):
    return create_user(db, user_data)


def list_users(db):
    return get_all_users(db)


def retrieve_user(db, user_id):
    return get_user_by_id(db, user_id)


def edit_user(db, user_id, user_data):
    return update_user(db, user_id, user_data)


def follow(db, user_id, target_id):
    return follow_user(db, user_id, target_id)


def unfollow(db, user_id, target_id):
    return unfollow_user(db, user_id, target_id)