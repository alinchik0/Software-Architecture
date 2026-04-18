from app.services.post_service import (
    create_post,
    get_all_posts,
    get_post_by_id,
    delete_post,
    like_post,
    get_feed
)


def publish_post(db, post_data):
    return create_post(db, post_data)


def list_posts(db):
    return get_all_posts(db)


def retrieve_post(db, post_id):
    return get_post_by_id(db, post_id)


def remove_post(db, post_id):
    return delete_post(db, post_id)


async def like(db, post_id, user_id):
    return await like_post(db, post_id, user_id)


def feed(db, user_id):
    return get_feed(db, user_id)