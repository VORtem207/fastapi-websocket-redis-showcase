import pytest

from ..user_helpers import authenticate_user


@pytest.mark.parametrize("username, password, expected", [
    ("alice", "secrettt", True),
    ("testuser", "wrongpass", False),
    ("nonexistent", "anypass", False),
    ("", "", False),
    ("testuser", "", False),
    ("", "testpass", False),
])
def test_authenticate_user(fake_db, username, password, expected):
    result = authenticate_user(fake_db, username, password)

    if expected:
        # Если ожидаем успех, проверяем что вернулся объект пользователя
        assert result is not False
        assert result.username == username  # или какое поле есть у твоего User
    else:
        # Если ожидаем неудачу, проверяем что вернулся False
        assert result is False
