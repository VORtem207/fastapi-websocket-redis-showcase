import jwt

from config import settings

from datetime import (
    datetime,
    timedelta,
    timezone,
)
from custom_logger.base import (
    get_logger,
    LoggerType,
)


DELAY_FOR_TOKEN_EXPIRATION: int = 15


logger = get_logger(LoggerType.default)


def create_access_token(input_user_data: dict, expires_delta: timedelta | None = None):
    logger.info("Creating access token.")
    to_encode = input_user_data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=DELAY_FOR_TOKEN_EXPIRATION)
    logger.debug("Setting expiration date.")
    to_encode.update({"exp": expire})
    logger.debug("Encoding token.")
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    logger.info("Access token created successfully.")
    return encoded_jwt
