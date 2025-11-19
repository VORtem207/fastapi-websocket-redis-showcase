
from models import User
from typing import Annotated
from auth.user_helpers import get_current_active_user

from fastapi import (
    APIRouter,
    Depends,
)


router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get("/me", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user
