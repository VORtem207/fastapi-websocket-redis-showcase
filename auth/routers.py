from fastapi.security import OAuth2PasswordRequestForm
from database import get_user_db
from datetime import timedelta
from typing import Annotated
from auth.auth import create_access_token
from auth.user_helpers import authenticate_user
from config import settings

from fastapi import (
    HTTPException,
    status,
    APIRouter,
    Depends,
)
from auth.models import (
    Token,
    UserRegister,
)


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(get_user_db(), form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        input_user_data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@router.post("/register")
async def register_user(user: UserRegister, user_db: dict = Depends(get_user_db)):
    if user.username in user_db:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")

    for existing_user in user_db.values():
        if existing_user["email"] == user.email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user_db[user.username] = {
        "username": user.username,
        "email": user.email,
        "full_name": None,
        "hashed_password": user.password,
        "disabled": False,
    }

    return {"message": "User successfully created"}
