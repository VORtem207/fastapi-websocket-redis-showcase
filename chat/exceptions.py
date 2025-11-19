
class WebSocketManagerError(Exception):
    """Custom exception for WebSocket Manager errors."""


class UserNotFoundError(WebSocketManagerError):
    def __init__(self, username: str):
        self.username = username
        super().__init__(f"User '{username}' not found in active connections")


class ConnectionAlreadyExistsError(WebSocketManagerError):
    def __init__(self, username: str):
        self.username = username
        super().__init__(f"Connection for user '{username}' already exists")
