import pytest

from ..user_helpers import verify_password


@pytest.mark.parametrize("password_hash,stored_hash,expected", [
    ("12345678", "12345678", True),
    ("12345678", "23456789", False),
    ("", "stored_hash", False),
    ("password_hash", "", False),
    ("", "", False),
    (None, "stored_hash", False),
    ("password_hash", None, False),
    (None, None, False),
])
def test_verify_password(password_hash, stored_hash, expected):
    assert verify_password(password_hash, stored_hash) is expected
