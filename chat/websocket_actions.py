
from fastapi import WebSocket
from chat.connection_manager import manager
from chat.models import ContentMessage

from typing import (
    Callable,
    Dict,
    Any,
)
from custom_logger.base import (
    get_logger,
    LoggerType,
)


MessageHandler = Callable[[WebSocket, ContentMessage], Any]
HandlersMap = Dict[str, MessageHandler]

message_handlers: HandlersMap = {}
logger = get_logger(LoggerType.default)


def message_handler(subtype: str):
    def decorator(func: MessageHandler):
        message_handlers[subtype] = func
        return func
    return decorator


@message_handler("broadcast")
async def handle_broadcast_message(websocket: WebSocket, message: ContentMessage) -> None:
    logger.info("Broadcast handler invoked")
    sender_username = message.sender_username
    message_text = message.message_text

    if not sender_username or not message_text:
        await websocket.send_text("Invalid message format: 'sender_username' and 'message_text' required.")
        return
    await manager.broadcast(f"#{sender_username} сказанул: {message_text}", sender_username)
    # await manager.update_ttl_for_username(sender_username, ONE_HOUR_IN_SECONDS)
    logger.info("Broadcast message sent")


@message_handler("private")
async def handle_private_message(websocket: WebSocket, message: ContentMessage) -> None:
    logger.info("Private message handler invoked")
    recipient_username = message.recipient_username
    message_text = message.message_text

    if not recipient_username or not message_text:
        logger.error("Invalid message format: 'recipient_username' and 'message_text' required.")
        return

    try:
        await manager.get_recipient_for_private_message(recipient_username, message_text)

    except ValueError:
        await websocket.send_text(f"User '{recipient_username}' not found in active connections.")
        return

    # for recipient in recipients:
    #     await recipient.send_text(f"#{message.sender_username} сказанул: {message_text}")
    # await manager.update_ttl_for_username(message.sender_username, ONE_HOUR_IN_SECONDS)
    logger.info("Private message sent")


def get_message_handler(response_type: str) -> MessageHandler | None:
    logger.info(f"Getting message handler for response type: {response_type}")
    return message_handlers.get(response_type)
