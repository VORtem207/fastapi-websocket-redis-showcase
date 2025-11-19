import asyncio
import json
import uuid
import os

from starlette.websockets import WebSocketState
from typing import Optional
from fastapi import WebSocket
from dotenv import load_dotenv
from redis import asyncio as aioredis
from config import settings

from custom_logger.base import (
    get_logger,
    LoggerType,
)
from abc import (
    ABC,
    abstractmethod,
)

load_dotenv()

logger = get_logger(LoggerType.default)

CURRENT_INSTANCE_ID = os.getenv("INSTANCE_ID", str(uuid.uuid4()))


class ConnectionManager(ABC):
    @abstractmethod
    async def connect(self, websocket: WebSocket, username: str) -> None:
        ...

    @abstractmethod
    async def disconnect(self, websocket: WebSocket) -> None:
        ...

    # @abstractmethod
    # async def update_ttl_for_username(self, username: str, ttl: int) -> None:
    #     ...

    @abstractmethod
    async def get_recipient_for_private_message(self, recipient_username: str, text_of_user_message: str) -> None:
        ...

    @abstractmethod
    async def broadcast(self,  message: str, sender_username: Optional[str] = None) -> None:
        ...

    @abstractmethod
    async def start(self) -> None:
        ...


class RedisConnectionManager(ConnectionManager):
    def __init__(
            self,
            redis_host: str = settings.redis_host,
            redis_port: int = settings.redis_port,
            current_instance_id: str = CURRENT_INSTANCE_ID

    ) -> None:
        self.redis: aioredis.Redis = aioredis.Redis(
            host=redis_host,
            port=redis_port,
        )
        self.local_connections: dict[str, WebSocket] = {}
        self.pubsub = self.redis.pubsub()
        self._listener_started = False

    async def _start_listener(self) -> None:
        await self.pubsub.subscribe(f"instance:{CURRENT_INSTANCE_ID}")

        while True:
            try:
                message = await self.pubsub.get_message(ignore_subscribe_messages=True)
                if not message:
                    await asyncio.sleep(0.1)
                    continue

                data = json.loads(message["data"])
                session_id = data["session_id"]

                # Находим локальный вебсокет для этой сессии
                websocket = self.local_connections.get(session_id)
                if websocket:
                    await websocket.send_text(data["message"])

            except Exception as e:
                logger.error(f"Error in listener: {e}")
                await asyncio.sleep(1)

    async def start(self):
        if not self._listener_started:
            self._listener_started = True
            await asyncio.create_task(self._start_listener())

    async def connect(self, websocket: WebSocket, username: str) -> None:
        session_id = str(uuid.uuid4())

        try:
            tr = self.redis.pipeline()

            await tr.hset(
                f"session:{session_id}",
                mapping={
                    "username": username,
                    "instance_id": CURRENT_INSTANCE_ID,
                }
            )
            await tr.sadd(f"user_sessions:{username}", session_id)
            await tr.sadd(f"instance_sessions:{CURRENT_INSTANCE_ID}", session_id)

            await tr.execute()

            await websocket.accept()
            self.local_connections[session_id] = websocket

        except Exception as e:
            logger.error(f"Failed to establish connection: {e}")
            await self.redis.delete(f"session:{session_id}")
            await self.redis.srem(f"user_sessions:{username}", session_id)
            await self.redis.srem(f"instance_sessions:{CURRENT_INSTANCE_ID}", session_id)
            raise

    async def disconnect(self, websocket: WebSocket) -> None:
        session_id = await self._get_session_id(websocket)
        username = await self._get_username_by_session(session_id)

        tr = self.redis.pipeline()
        await tr.delete(f"session:{session_id}")
        await tr.srem(f"user_sessions:{username}", session_id)
        await tr.srem(f"instance_sessions:{CURRENT_INSTANCE_ID}", session_id)
        await tr.execute()

        self.local_connections.pop(session_id, None)

    async def _get_username_by_session(self, session_id: str) -> str:
        session_data = await self.redis.hgetall(f"session:{session_id}")
        if not session_data:
            raise ValueError(f"Session {session_id} not found")
        return session_data[b"username"].decode()

    async def _get_session_id(self, websocket: WebSocket) -> str:
        for session_id, ws in self.local_connections.items():
            if ws == websocket:
                return session_id
        raise ValueError("WebSocket not found in local connections")

    async def broadcast(self, message: str, sender_username: Optional[str] = None) -> None:
        # Получаем все существующие сессии для всех инстансов
        instance_pattern = "instance_sessions:*"
        all_instance_keys = await self.redis.keys(instance_pattern)
        all_sessions = set()

        # Собираем все сессии со всех инстансов
        for instance_key in all_instance_keys:
            sessions = await self.redis.smembers(instance_key)
            all_sessions.update({s.decode() for s in sessions})

        # Исключаем сессии отправителя, если он указан
        if sender_username:
            sender_sessions = await self.redis.smembers(f"user_sessions:{sender_username}")
            sender_sessions = {s.decode() for s in sender_sessions}
            all_sessions = all_sessions - sender_sessions

        # Для каждой сессии смотрим её инстанс
        for session_id in all_sessions:
            session_data = await self.redis.hgetall(f"session:{session_id}")
            if not session_data:
                continue

            instance_id = session_data[b"instance_id"].decode()

            if instance_id == CURRENT_INSTANCE_ID:
                # Если наш инстанс - отправляем через локальный вебсокет
                websocket = self.local_connections.get(session_id)
                if websocket:
                    try:
                        await websocket.send_text(message)
                    except Exception as e:
                        logger.error(f"Failed to send broadcast to {session_id}: {e}")
            else:
                # Если другой инстанс - публикуем в его канал
                try:
                    await self.redis.publish(
                        f"instance:{instance_id}",
                        json.dumps({
                            "session_id": session_id,
                            "message": message,
                            "type": "broadcast"
                        })
                    )
                except Exception as e:
                    logger.error(f"Failed to publish broadcast to instance {instance_id}: {e}")

    async def get_recipient_for_private_message(
            self,
            recipient_username: str,
            text_of_user_message: str = None,
    ) -> None:
        logger.info(f"Starting to process private message for recipient: {recipient_username}")

        user_sessions = await self.redis.smembers(f"user_sessions:{recipient_username}")
        logger.debug(f"Found {len(user_sessions)} active sessions for user {recipient_username}")

        if not user_sessions:
            logger.error(f"No active sessions found for user {recipient_username}")
            raise ValueError(f"No active sessions for user {recipient_username}")

        for session_id in user_sessions:
            session_id = session_id.decode()
            logger.debug(f"Processing session: {session_id}")

            session_data = await self.redis.hgetall(f"session:{session_id}")
            instance_id = session_data[b"instance_id"].decode()
            logger.debug(f"Session {session_id} belongs to instance {instance_id}")

            if instance_id == CURRENT_INSTANCE_ID:
                websocket = self.local_connections.get(session_id)
                if websocket:
                    try:
                        # Проверяем, что соединение открыто
                        if websocket.client_state == WebSocketState.CONNECTED:  # Нужно импортировать WebSocketState
                            logger.debug(f"Found active websocket for session {session_id}, sending message")
                            await websocket.send_text(f"Cказанул: {text_of_user_message}")
                            logger.debug(f"Message sent to local websocket for session {session_id}")
                        else:
                            logger.debug(f"Websocket for session {session_id} is closed, cleaning up")
                            # Очищаем недействительное соединение
                            self.local_connections.pop(session_id)
                            # Удаляем сессию из Redis
                            await self._cleanup_session(session_id)
                    except Exception as e:
                        logger.error(f"Error sending message to session {session_id}: {e}")
                        # Очищаем при ошибке отправки
                        self.local_connections.pop(session_id)
                        await self._cleanup_session(session_id)
            else:
                # Если на другом - публикуем в канал того инстанса
                logger.debug(f"Publishing message to instance {instance_id} for session {session_id}")
                await self.redis.publish(
                    f"instance:{instance_id}",
                    json.dumps({
                        "session_id": session_id,
                        "message": text_of_user_message,
                        "type": "private_message"
                    })
                )
                logger.debug(f"Message published to instance {instance_id}")

        logger.info(f"Finished processing private message for recipient: {recipient_username}")

    async def _cleanup_session(self, session_id: str) -> None:
        """Очистка данных сессии из Redis"""
        try:
            session_data = await self.redis.hgetall(f"session:{session_id}")
            if session_data:
                username = session_data[b"username"].decode()
                tr = self.redis.pipeline()
                await tr.delete(f"session:{session_id}")
                await tr.srem(f"user_sessions:{username}", session_id)
                await tr.srem(f"instance_sessions:{CURRENT_INSTANCE_ID}", session_id)
                await tr.execute()
                logger.debug(f"Cleaned up session data for {session_id}")
        except Exception as e:
            logger.error(f"Error cleaning up session {session_id}: {e}")


manager: ConnectionManager = RedisConnectionManager()
