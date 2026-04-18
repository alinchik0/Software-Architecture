from app.services.auth_service import (
    authenticate_user,
    issue_access_token,
    get_user_from_token,
)


def login_user(db, username: str, password: str):
    user = authenticate_user(db, username, password)
    if not user:
        return None

    token = issue_access_token(user)
    return {"access_token": token, "token_type": "bearer"}


def get_authenticated_user(db, token: str):
    return get_user_from_token(db, token)
