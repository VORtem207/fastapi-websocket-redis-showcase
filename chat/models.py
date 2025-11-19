from typing import Optional, Literal
from pydantic import BaseModel


class ContentMessage(BaseModel):
    message_text: str
    recipient_username: Optional[str] = None
    sender_username: Optional[str] = None


class WebSocketMessage(BaseModel):
    response_type: Literal[
        "private",
        "broadcast",
    ]
    content_of_message: ContentMessage
    timestamp: Optional[str] = None
