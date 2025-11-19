###TO DO: Центральное подключение к базе данных
from typing import Any

fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "secret",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Smith",
        "email": "alice@example.com",
        "hashed_password": "secret",
        "disabled": False,
    },
}


def get_user_db() -> dict[str, dict[str, Any]]:
    return fake_users_db
