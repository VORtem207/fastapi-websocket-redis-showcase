import json

from pydantic import ValidationError
from chat.connection_manager import manager
from chat.models import WebSocketMessage
from chat.websocket_actions import get_message_handler
from chat.websocket_helpers import get_username

from fastapi import (
    WebSocket,
    WebSocketDisconnect,
    APIRouter,
)
from custom_logger.base import (
    get_logger,
    LoggerType,
)


router = APIRouter()
logger = get_logger(LoggerType.default)


def normalize_message_data(raw_message) -> dict:
    converted_data_to_dict = {}
    if isinstance(raw_message, str):
        try:
            converted_data_to_dict = json.loads(raw_message)
        except json.JSONDecodeError:
            logger.error(f"Error parsing WebSocket message: {raw_message}")

    elif isinstance(raw_message, dict):
        converted_data_to_dict = raw_message

    return converted_data_to_dict


async def parse_message(raw_message: str, username: str) -> WebSocketMessage:
    message = normalize_message_data(raw_message)
    parsed_message = WebSocketMessage(**message)

    parsed_message.content_of_message.sender_username = username
    return parsed_message


async def handle_message(websocket: WebSocket, username: str, raw_message: str) -> None:
    try:
        parsed_message = await parse_message(raw_message, username)
    except ValidationError as validation_error:
        logger.error(f"Error parsing WebSocket message: {validation_error}")
        return

    message_handler = get_message_handler(parsed_message.response_type)

    if message_handler:
        logger.debug(f"Calling handler: {message_handler.__name__}")
        await message_handler(websocket, parsed_message.content_of_message)
    else:
        logger.error(f"No handler found for response_type: {parsed_message.response_type}")


async def handle_connection_start(websocket: WebSocket, username: str) -> None:
    await manager.connect(websocket, username)
    await manager.broadcast(f"#{username} залетел")


async def handle_connection_end(websocket: WebSocket, username: str) -> None:
    await manager.disconnect(websocket)
    await manager.broadcast(f"#{username} упокоился", sender_username=username)


async def process_websocket_messages(websocket: WebSocket, username: str) -> None:
    running = True

    while running:
        try:
            raw_message = await websocket.receive_text()
        except WebSocketDisconnect:
            await handle_connection_end(websocket, username)
            running = False
            break

        if running:
            await handle_message(websocket, username, raw_message)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    username = await get_username(websocket)

    await handle_connection_start(websocket, username)
    await process_websocket_messages(websocket, username)
