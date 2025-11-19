import jwt

from typing import Annotated
from jwt.exceptions import InvalidTokenError
from database import fake_users_db
from models import User
from auth.models import TokenData
from auth.database import get_user
from auth.auth_helpers import verify_password
from fastapi.security import OAuth2PasswordBearer
from config import settings

from fastapi import (
    Depends,
    HTTPException,
    status,
)
from custom_logger.base import (
    get_logger,
    LoggerType,
)


logger = get_logger(LoggerType.default)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def authenticate_user(fake_db, username: str, password: str):
    logger.info("Authenticating user.")
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    logger.info("User authenticated successfully.")
    return user


def get_credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def extract_username(payload: dict) -> str:
    username: str = payload.get("sub")
    if username is None:
        raise InvalidTokenError
    return username


async def decode_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except InvalidTokenError:
        raise get_credentials_exception()

    try:
        username = extract_username(payload)
    except InvalidTokenError:
        raise get_credentials_exception()

    return TokenData(username=username)


async def get_user_from_db(username: str) -> User:
    user = get_user(fake_users_db, username=username)
    if user is None:
        raise get_credentials_exception()
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    logger.info("Getting current user.")
    token_data = await decode_token(token)
    user = await get_user_from_db(token_data.username)
    logger.info("Current user retrieved successfully.")
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user
