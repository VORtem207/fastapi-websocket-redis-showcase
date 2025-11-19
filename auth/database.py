from models import UserInDB


def get_user(db, username: str) -> UserInDB | None:
    if username in db:
        user_dict = db.get(username)
        return UserInDB(**user_dict)
