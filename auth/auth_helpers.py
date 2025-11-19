from custom_logger.base import (
    get_logger,
    LoggerType,
)

logger = get_logger(LoggerType.default)


def verify_password(password_hash: str, stored_hash: str) -> bool:
    """Compare password hashes.

        Args:
            password_hash: Hash of password from frontend
            stored_hash: Hash stored in database
    """
    if not password_hash or not stored_hash:
        logger.error("Password verification failed: empty hash")
        return False

    return password_hash == stored_hash
