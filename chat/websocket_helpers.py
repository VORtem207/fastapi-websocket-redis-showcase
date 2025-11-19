from auth.user_helpers import get_current_user

from fastapi import (
    WebSocket,
    HTTPException,
)
from custom_logger.base import (
    get_logger,
    LoggerType,
)


logger = get_logger(LoggerType.default)


async def get_username(websocket: WebSocket) -> str:
    token = websocket.headers.get("Token")
    if not token:
        # await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        logger.error("Token not found in headers")

    # try:
    #     current_user = await get_current_user(token)
    #     username = current_user.username
    #     return username
    # except HTTPException:
    #     logger.error("Failed to get username from token")
    #     await websocket.close()
    try:
        current_user = await get_current_user(token)
    except HTTPException:
        logger.error("Failed to get username from token")
        await websocket.close()
        return "NoNe"

    username = current_user.username
    return username

    # raise ValueError("Invalid token")
